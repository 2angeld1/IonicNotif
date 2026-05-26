import json
from google import genai
from google.genai import types
import cohere
from app.config import get_settings, GEMINI_MODELS, COHERE_MODELS
from app.services.translator.php_translator import PHPTranslator
from app.services.translator.js_to_ts_translator import JSToTSConverter
from app.services.translator.verso_cache import VersoCache


TRADUCTION_PROMPT = """
Eres un experto traductor de código fuente. Tu tarea es traducir código de {source_lang} a {target_lang}.

REGLAS:
1. Traduce TODO el código, preservando la lógica exacta.
2. Usa las convenciones y mejores prácticas del lenguaje destino.
3. Preserva comentarios (tradúcelos al inglés si están en otro idioma).
4. Preserva strings literales y mensajes al usuario sin traducir.
5. Responde ÚNICAMENTE con el código traducido, sin markdown, sin explicaciones.
6. No uses bloques ``` ni etiquetas de lenguaje.
7. Si el código destino usa imports/librerías equivalentes, inclúyelos.
8. Maneja casos edge: código vacío, errores de sintaxis, etc.

Código fuente ({source_lang} v{source_version}):
```{source_lang}
{source_code}
```

Traduce a {target_lang} v{target_version}:
"""

SAME_LANG_PAIRS = {
    ("PHP", "PHP"),
    ("JAVASCRIPT", "TypeScript"),
    ("JS", "TS"),
    ("JAVASCRIPT", "TS"),
    ("JS", "TypeScript"),
}


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

        cache_key_source = source_lang.upper() + target_lang.upper()

        # Check cache first
        cached = await VersoCache.get(source, source_lang, target_lang, target_version)
        if cached is not None:
            return {
                "result": cached,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_version": source_version,
                "target_version": target_version,
                "method": "cache",
            }

        # Same-language migration (rules-based, deterministic)
        if (source_lang_norm, target_lang_norm) in SAME_LANG_PAIRS or (
            source_lang_norm.upper() == target_lang_norm.upper()
        ):
            result = self._rules_translate(source, source_lang_norm)
            await VersoCache.store(source, source_lang, target_lang, target_version, result, "rules")
            return {
                "result": result,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "source_version": source_version,
                "target_version": target_version,
                "method": "rules",
            }

        # Cross-language: AI cascade
        result, model_used = await self._ai_cascade(
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
                "warning": "AI translation failed, used regex rules as fallback",
            }

        await VersoCache.store(source, source_lang, target_lang, target_version, result, model_used)
        return {
            "result": result,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "source_version": source_version,
            "target_version": target_version,
            "method": model_used,
        }

    def _rules_translate(self, code: str, lang: str) -> str:
        if lang in ("PHP",):
            return self.php.translate(code)
        if lang in ("JAVASCRIPT", "JS"):
            return self.jsts.convert(code)
        return code

    async def _ai_cascade(
        self, source: str, source_lang: str, target_lang: str, source_version: str, target_version: str
    ) -> tuple[str | None, str | None]:
        settings = get_settings()
        prompt = TRADUCTION_PROMPT.format(
            source_lang=source_lang,
            target_lang=target_lang,
            source_version=source_version or "latest",
            target_version=target_version or "latest",
            source_code=source,
        )

        # 1. Try Gemini cascade
        if settings.muelle_gemini_api_key or settings.kitchy_gemini_api_key:
            api_key = settings.muelle_gemini_api_key or settings.kitchy_gemini_api_key
            try:
                client = genai.Client(api_key=api_key)
                for model_name in GEMINI_MODELS:
                    try:
                        response = await client.aio.models.generate_content(
                            model=model_name,
                            contents=[prompt],
                            config=types.GenerateContentConfig(
                                temperature=0.1,
                                max_output_tokens=8192,
                            ),
                        )
                        text = response.text.strip()
                        text = self._clean_ai_output(text)
                        if text:
                            return text, f"gemini:{model_name}"
                    except Exception as e:
                        print(f"[Verso] Gemini {model_name} falló: {e}")
                        continue
            except Exception as e:
                print(f"[Verso] Error inicializando Gemini: {e}")

        # 2. Try Cohere cascade
        if settings.cohere_api_key:
            try:
                co_client = cohere.ClientV2(api_key=settings.cohere_api_key)
                for model_name in COHERE_MODELS:
                    try:
                        response = co_client.chat(
                            model=model_name,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=0.0,
                        )
                        text = response.message.content[0].text.strip()
                        text = self._clean_ai_output(text)
                        if text:
                            return text, f"cohere:{model_name}"
                    except Exception as e:
                        print(f"[Verso] Cohere {model_name} falló: {e}")
                        continue
            except Exception as e:
                print(f"[Verso] Error inicializando Cohere: {e}")

        return None, None

    @staticmethod
    def _clean_ai_output(text: str) -> str:
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        return text.strip()
