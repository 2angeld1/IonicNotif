import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.translator.verso_translator import HybridTranslator
from app.services.translator.github_reader import GitHubRepoReader, GitHubReaderError
from app.services.translator.verso_cache import VersoCache
from app.config import get_settings

router = APIRouter(prefix="/api/translator", tags=["translator"])

translator = HybridTranslator()
github_reader = GitHubRepoReader(token=get_settings().github_token or None)


class TranslateRequest(BaseModel):
    source: str
    source_lang: str = ""
    target_lang: str = "Python"
    source_version: str = ""
    target_version: str = ""


class TranslateRepoRequest(BaseModel):
    repo_url: str
    source_lang: Optional[str] = None
    target_lang: str = "Python"
    target_version: str = ""
    branch: Optional[str] = None


class FileTranslation(BaseModel):
    path: str
    language: str
    original: str
    translated: str
    method: str


class TranslateResponse(BaseModel):
    result: str
    source_lang: str
    target_lang: str
    source_version: str
    target_version: str
    method: str
    lines_input: int = 0
    lines_output: int = 0


@router.post("/translate")
async def translate_code(req: TranslateRequest):
    if not req.source.strip():
        raise HTTPException(400, "Código fuente vacío")

    source_lang = req.source_lang
    if not source_lang:
        try:
            detect_resp = await detect_language({"code": req.source})
            source_lang = detect_resp["language"]
        except HTTPException:
            raise HTTPException(400, "No se pudo detectar el lenguaje automáticamente. Especifica el lenguaje origen.")
        except Exception as e:
            raise HTTPException(500, f"Error detectando lenguaje: {str(e)}")

    lines_in = req.source.count("\n") + 1

    try:
        result = await translator.translate(
            source=req.source,
            source_lang=source_lang,
            target_lang=req.target_lang or source_lang,
            source_version=req.source_version,
            target_version=req.target_version,
        )
    except Exception as e:
        raise HTTPException(500, f"Error en traducción: {str(e)}")

    lines_out = result["result"].count("\n") + 1

    return TranslateResponse(
        result=result["result"],
        source_lang=result["source_lang"],
        target_lang=result["target_lang"],
        source_version=result["source_version"],
        target_version=result["target_version"],
        method=result["method"],
        lines_input=lines_in,
        lines_output=lines_out,
    )


@router.post("/translate-repo")
async def translate_repo(req: TranslateRepoRequest):
    try:
        files = await github_reader.list_files(req.repo_url)
    except GitHubReaderError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error al leer repositorio: {str(e)}")

    if not files:
        raise HTTPException(400, "No se encontraron archivos traducibles en el repositorio")

    translations: list[FileTranslation] = []

    for f in files:
        if req.source_lang and f.language.upper() != req.source_lang.upper():
            translations.append(FileTranslation(
                path=f.path,
                language=f.language,
                original=f.content,
                translated=f"# SKIPPED: language {f.language} != {req.source_lang}",
                method="skipped",
            ))
            continue

        try:
            result = await translator.translate(
                source=f.content,
                source_lang=f.language,
                target_lang=req.target_lang,
                target_version=req.target_version,
            )
            translations.append(FileTranslation(
                path=f.path,
                language=f.language,
                original=f.content,
                translated=result["result"],
                method=result["method"],
            ))
        except Exception as e:
            translations.append(FileTranslation(
                path=f.path,
                language=f.language,
                original=f.content,
                translated=f"# ERROR: {str(e)}",
                method="error",
            ))

    return {
        "repo_url": req.repo_url,
        "total_files": len(files),
        "translated": len([t for t in translations if t.method not in ("skipped", "error")]),
        "skipped": len([t for t in translations if t.method == "skipped"]),
        "errors": len([t for t in translations if t.method == "error"]),
        "files": translations,
    }


@router.get("/languages")
async def supported_languages():
    return {
        "PHP": {
            "label": "PHP",
            "source_versions": ["5.6", "7.0", "7.1", "7.2", "7.3", "7.4"],
            "target_versions": ["8.0", "8.1", "8.2", "8.3", "8.4", "8.5"],
            "target_lang": "PHP",
            "can_translate_to": ["Python", "JavaScript", "Go", "Java", "Rust", "C#", "Ruby", "TypeScript", "COBOL", "C++"],
        },
        "JAVASCRIPT": {
            "label": "JavaScript",
            "source_versions": ["ES5", "ES6", "ES2016+"],
            "target_versions": ["TS 5.x"],
            "target_lang": "TypeScript",
            "can_translate_to": ["Python", "Go", "Java", "Rust", "TypeScript", "PHP", "C#", "Ruby", "COBOL", "C++"],
        },
        "PYTHON": {
            "label": "Python",
            "source_versions": ["2.7", "3.6", "3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13"],
            "target_versions": ["3.11", "3.12", "3.13"],
            "target_lang": "Python",
            "can_translate_to": ["Go", "JavaScript", "Rust", "Java", "C#", "Ruby", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "JAVA": {
            "label": "Java",
            "source_versions": ["8", "11", "17", "21"],
            "target_versions": ["17", "21"],
            "target_lang": "Java",
            "can_translate_to": ["Python", "JavaScript", "Go", "Rust", "Kotlin", "C#", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "GO": {
            "label": "Go",
            "source_versions": ["1.16", "1.17", "1.18", "1.19", "1.20", "1.21", "1.22"],
            "target_versions": ["1.22", "1.23"],
            "target_lang": "Go",
            "can_translate_to": ["Python", "JavaScript", "Java", "Rust", "C#", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "RUST": {
            "label": "Rust",
            "source_versions": ["2015", "2018", "2021", "2024"],
            "target_versions": ["2021", "2024"],
            "target_lang": "Rust",
            "can_translate_to": ["Python", "JavaScript", "Go", "Java", "Rust", "C#", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "TYPESCRIPT": {
            "label": "TypeScript",
            "source_versions": ["ES5", "ES6", "ES2016+", "TS 3.x", "TS 4.x", "TS 5.x"],
            "target_versions": ["5.x"],
            "target_lang": "TypeScript",
            "can_translate_to": ["Python", "JavaScript", "Go", "Java", "Rust", "C#", "PHP", "Ruby", "COBOL", "C++"],
        },
        "COBOL": {
            "label": "COBOL",
            "source_versions": ["COBOL-85", "COBOL-2002", "COBOL-2014"],
            "target_versions": ["COBOL-2002", "COBOL-2014"],
            "target_lang": "COBOL",
            "can_translate_to": ["Python", "Java", "C#", "Go", "Rust", "PHP", "JavaScript", "TypeScript", "C++"],
        },
        "CPP": {
            "label": "C++",
            "source_versions": ["C++98", "C++11", "C++14", "C++17", "C++20", "C++23"],
            "target_versions": ["C++17", "C++20", "C++23"],
            "target_lang": "C++",
            "can_translate_to": ["Python", "Java", "C#", "Go", "Rust", "PHP", "JavaScript", "TypeScript", "COBOL"],
        },
        "CSHARP": {
            "label": "C#",
            "source_versions": ["7.x", "8", "9", "10", "11", "12"],
            "target_versions": ["10", "11", "12"],
            "target_lang": "C#",
            "can_translate_to": ["Python", "JavaScript", "Go", "Java", "Rust", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "RUBY": {
            "label": "Ruby",
            "source_versions": ["2.7", "3.0", "3.1", "3.2", "3.3"],
            "target_versions": ["3.0", "3.1", "3.2", "3.3"],
            "target_lang": "Ruby",
            "can_translate_to": ["Python", "JavaScript", "Go", "Java", "Rust", "PHP", "TypeScript", "COBOL", "C++"],
        },
        "KOTLIN": {
            "label": "Kotlin",
            "source_versions": ["1.6", "1.8", "2.0"],
            "target_versions": ["1.8", "2.0"],
            "target_lang": "Kotlin",
            "can_translate_to": ["Java", "Python", "JavaScript", "Go", "TypeScript", "COBOL", "C++"],
        },
    }


@router.post("/detect")
async def detect_language(body: dict):
    code = body.get("code", "")
    if not code.strip():
        raise HTTPException(400, "Código vacío")

    try:
        rust_core_url = os.getenv("RUST_CORE_URL", "http://localhost:8002")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{rust_core_url}/detect", json={"source": code})
            if resp.is_success:
                data = resp.json()
                return {"language": data["language"], "confidence": 1, "scores": {}}
    except Exception as e:
        print(f"[Verso] Rust detect falló, usando fallback: {e}")

    raise HTTPException(400, "No se pudo detectar el lenguaje")


@router.get("/cache/stats")
async def cache_stats():
    return await VersoCache.stats()
