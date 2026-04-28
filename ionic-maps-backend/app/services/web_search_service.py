
from duckduckgo_search import DDGS
import json

class WebSearchService:
    """
    Servicio de búsqueda libre (DuckDuckGo) para Caitlyn.
    Optimizado para funcionar como fallback cuando Gemini Search se agota.
    """

    @staticmethod
    def search_panama_prices(query: str, max_results: int = 5):
        print(f"🔎 [FALLBACK-SEARCH] Intentando búsqueda en internet: {query}")
        
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, region='pa-es', safesearch='off', timelimit='m', max_results=max_results)
                
                if not results:
                    return []

                formatted_results = []
                for r in results:
                    formatted_results.append({
                        "title": r.get("title"),
                        "snippet": r.get("body"),
                        "link": r.get("href")
                    })
                
                return formatted_results
        except Exception as e:
            print(f"⚠️ [FALLBACK-SEARCH] Error en DuckDuckGo: {e}")
            return []
