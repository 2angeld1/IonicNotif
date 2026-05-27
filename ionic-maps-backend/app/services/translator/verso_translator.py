import json
import os
import logging
import httpx
from app.services.translator.php_translator import PHPTranslator
from app.services.translator.js_to_ts_translator import JSToTSConverter
from app.services.translator.verso_cache import VersoCache
from app.config import get_settings, GEMINI_MODELS, COHERE_MODELS

RUST_CORE_URL = os.getenv("RUST_CORE_URL", "http://localhost:8002")

logger = logging.getLogger("verso")


class HybridTranslator:

    def __init__(self):
        self.php = PHPTranslator()
        self.jsts = JSToTSConverter()

    async def translate(
        self,
        source: str,
        source_lang: str,
        target_lang: str,
        source_version: str = "",
        target_version: str = "",
    ) -> dict:
        source_lang_norm = source_lang.upper()
        target_lang_norm = target_lang.upper()

        logger.info("translate: %s -> %s (lines=%d)", source_lang, target_lang, source.count("\n") + 1)

        # Check cache first
        cached = await VersoCache.get(source, source_lang, target_lang, target_version)
        if cached is not None:
            logger.info("cache HIT: %s -> %s", source_lang, target_lang)
            return {
                "result": cached,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_version": source_version,
                "target_version": target_version,
                "method": "cache",
            }

        logger.info("cache MISS: %s -> %s", source_lang, target_lang)

        # Same-language migration (rules-based, deterministic)
        if source_lang_norm == target_lang_norm:
            result = self._rules_translate(source, source_lang_norm)
            await VersoCache.store(source, source_lang, target_lang, target_version, result, "rules")
            logger.info("rules: %s -> %s (same-language)", source_lang, target_lang)
            return {
                "result": result,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_version": source_version,
                "target_version": target_version,
                "method": "rules",
            }

        # Cross-language: delegate to Rust core
        result, method = await self._rust_translate(
            source, source_lang, target_lang, source_version, target_version
        )

        if result is None:
            # Last resort: rules anyway (partial)
            fallback_result = self._rules_translate(source, source_lang_norm)
            await VersoCache.store(source, source_lang, target_lang, target_version, fallback_result, "rules_fallback")
            return {
                "result": fallback_result,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_version": source_version,
                "target_version": target_version,
                "method": "rules_fallback",
                "warning": "Rust core falló, usado reglas como fallback",
            }

        await VersoCache.store(source, source_lang, target_lang, target_version, result, method)
        return {
            "result": result,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_version": source_version,
            "target_version": target_version,
            "method": method,
        }

    async def _rust_translate(
        self, source: str, source_lang: str, target_lang: str,
        source_version: str, target_version: str
    ) -> tuple[str | None, str | None]:
        settings = get_settings()
        gemini_key = settings.muelle_gemini_api_key or settings.kitchy_gemini_api_key
        cohere_key = settings.cohere_api_key

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Gemini cascade
            if gemini_key:
                for model in GEMINI_MODELS:
                    try:
                        logger.info("rust call: gemini %s %s -> %s", model, source_lang, target_lang)
                        resp = await client.post(f"{RUST_CORE_URL}/translate", json={
                            "source": source,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "source_version": source_version or None,
                            "target_version": target_version or None,
                            "gemini_key": gemini_key,
                            "gemini_model": model,
                        }, timeout=120.0)
                        if resp.is_success:
                            data = resp.json()
                            if data.get("result"):
                                logger.info("gemini %s SUCCESS: %s -> %s", model, source_lang, target_lang)
                                return data["result"], data["method"]
                    except Exception as e:
                        logger.warning("gemini %s FAILED: %s", model, e)
                        continue

            # Cohere cascade
            if cohere_key:
                for model in COHERE_MODELS:
                    try:
                        logger.info("rust call: cohere %s %s -> %s", model, source_lang, target_lang)
                        resp = await client.post(f"{RUST_CORE_URL}/translate", json={
                            "source": source,
                            "source_lang": source_lang,
                            "target_lang": target_lang,
                            "source_version": source_version or None,
                            "target_version": target_version or None,
                            "cohere_key": cohere_key,
                            "cohere_model": model,
                        }, timeout=120.0)
                        if resp.is_success:
                            data = resp.json()
                            if data.get("result"):
                                logger.info("cohere %s SUCCESS: %s -> %s", model, source_lang, target_lang)
                                return data["result"], data["method"]
                    except Exception as e:
                        logger.warning("cohere %s FAILED: %s", model, e)
                        continue

        logger.warning("rust cascade ALL FAILED: %s -> %s", source_lang, target_lang)
        return None, None

    def _rules_translate(self, code: str, lang: str) -> str:
        if lang in ("PHP",):
            return self.php.translate(code)
        if lang in ("JAVASCRIPT", "JS"):
            return self.jsts.convert(code)
        return code
