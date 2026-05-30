from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.scrapers.docs_scraper_service import DocsScraperService

router = APIRouter()

class DocsRequest(BaseModel):
    source_lang: str
    target_lang: str
    source_version: str
    target_version: str

@router.post("/docs")
async def scrape_docs(req: DocsRequest):
    try:
        docs_text = await DocsScraperService.fetch_migration_docs(
            req.source_lang,
            req.target_lang,
            req.source_version,
            req.target_version
        )
        return {"status": "success", "docs_text": docs_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
