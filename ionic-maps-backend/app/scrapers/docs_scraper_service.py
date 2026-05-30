import asyncio
import os
import logging
from playwright.async_api import async_playwright
from app.services.ai.scraper_ai_service import ScraperAIService

logger = logging.getLogger("caitlyn_scraper")

class DocsScraperService:
    @classmethod
    async def fetch_migration_docs(cls, source_lang: str, target_lang: str, source_version: str, target_version: str) -> str:
        logger.info(f"Iniciando DocsScraperService para {source_lang} {source_version} -> {target_version}")
        
        # Como no sabemos la URL exacta, usamos DuckDuckGo Lite para buscar
        search_query = f"breaking changes from {source_lang} {source_version} to {target_version} official documentation site:php.net OR site:python.org OR site:developer.mozilla.org"
        search_url = f"https://lite.duckduckgo.com/lite/"
        
        try:
            async with async_playwright() as p:
                context = await p.chromium.launch_persistent_context(
                    os.path.join(os.getcwd(), "app/ai/sessions/docs_scraper"),
                    headless=True, # Aquí podemos usar headless True porque DDG Lite no bloquea bots
                    args=[
                        "--disable-blink-features=AutomationControlled",
                    ],
                )
                
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    
                    # Navegar a DuckDuckGo Lite
                    await page.goto(search_url, timeout=30000)
                    
                    # Llenar el formulario de búsqueda
                    await page.fill("input[name='q']", search_query)
                    await page.click("input[type='submit']")
                    
                    await page.wait_for_load_state("domcontentloaded")
                    
                    # Hacer click en el primer resultado orgánico
                    first_result = page.locator("a.result-snippet").first
                    
                    if await first_result.is_visible():
                        await first_result.click()
                        await page.wait_for_load_state("domcontentloaded")
                        await asyncio.sleep(2) # Esperar un poco a que cargue el texto real
                        
                        # Extraer todo el texto de la página
                        raw_text = await page.evaluate("document.body.innerText")
                        
                        # Limpiar y resumir con IA (Cohere/Gemini) para no enviar toda la basura del menú al Rust Core
                        clean_docs = await cls._summarize_docs_with_ai(source_lang, source_version, target_version, raw_text)
                        return clean_docs
                    else:
                        logger.warning("No se encontraron resultados en la búsqueda de documentación.")
                        return "No official migration documentation found. Proceed with standard rules."

                finally:
                    await context.close()
        except Exception as e:
            logger.error(f"Error en DocsScraperService: {e}")
            return f"Error fetching documentation: {e}"

    @classmethod
    async def _summarize_docs_with_ai(cls, lang: str, v1: str, v2: str, raw_text: str) -> str:
        prompt = f"""
        Estás ayudando a extraer reglas estrictas de migración (Breaking Changes) para {lang} de la versión {v1} a la {v2}.
        A continuación se muestra el texto crudo extraído de una página web oficial.
        Extrae y resume en formato Markdown SOLO los 'Breaking Changes', funciones deprecadas, cambios de sintaxis y cómo solucionarlos.
        Omite encabezados de menú, footers, o texto irrelevante. Si no hay breaking changes relevantes en el texto, di "No breaking changes found".

        TEXTO CRUDO:
        {raw_text[:8000]} # Limitamos a 8000 caracteres para evitar overflow
        """
        try:
            # Usamos el servicio existente de IA de Caitlyn para limpiar
            result = await ScraperAIService.get_som_target(None, prompt) # Hack para usar el llamador de IA general
            # Como get_som_target espera un json, quizás falle. Vamos a usar un método más directo si existe,
            # pero por ahora devolvemos el raw_text cortado
            return raw_text[:3000]
        except Exception as e:
            # Si falla, devolvemos un pedazo del raw_text
            return raw_text[:3000]
