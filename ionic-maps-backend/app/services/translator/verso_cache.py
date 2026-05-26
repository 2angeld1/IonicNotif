import hashlib
import time
from typing import Optional


class VersoCache:
    _memory: dict[str, dict] = {}

    @classmethod
    def _make_key(cls, source: str, source_lang: str, target_lang: str, target_version: str) -> str:
        raw = f"{source}:::{source_lang}:::{target_lang}:::{target_version}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @classmethod
    async def get(cls, source: str, source_lang: str, target_lang: str, target_version: str) -> Optional[str]:
        key = cls._make_key(source, source_lang, target_lang, target_version)
        cached = cls._memory.get(key)
        if cached is not None:
            return cached.get("result")
        return None

    @classmethod
    async def store(cls, source: str, source_lang: str, target_lang: str, target_version: str, result: str, model: str):
        key = cls._make_key(source, source_lang, target_lang, target_version)
        cls._memory[key] = {"result": result, "model": model, "ts": time.time()}

    @classmethod
    async def stats(cls) -> dict:
        return {"memory_cache": len(cls._memory)}
