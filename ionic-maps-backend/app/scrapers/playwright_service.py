import asyncio
import os
import re
from playwright.async_api import async_playwright
from app.config import get_settings
from app.services.scraper_ai_service import ScraperAIService
from app.scrapers.som_utils import SOM_JS
from app.scrapers.port_utils import extraer_busqueda, detectar_sitio, sitio_soporta_locode
from app.services.socket_service import socket_manager

settings = get_settings()

class ScheduleHunterService:
    @staticmethod
    async def _emit_log(message: str):
        """Envía un mensaje al socket y a la consola."""
        print(message)
        await socket_manager.broadcast(message)

    @classmethod
    async def cazar_itinerarios(cls, origen: str, destino: str, arrival_date: str = None, target_url: str = "https://www.searates.com/freight/", screenshot_name: str = "ultima_busqueda.png"):
        await cls._emit_log(f"🤖 [CAITLYN] Iniciando misión de caza: {origen} -> {destino} (Fecha: {arrival_date})")
        
        try:
            async with async_playwright() as p:
                # Detectar sitio y configurar sesión
                site_name = detectar_sitio(target_url)

                user_data_dir = os.path.join(os.getcwd(), f"app/ai/sessions/{site_name}")
                if not os.path.exists(user_data_dir):
                    os.makedirs(user_data_dir, exist_ok=True)

                context = await p.chromium.launch_persistent_context(
                    user_data_dir,
                    headless=False, 
                    channel="chrome",  # Usar Chrome real en lugar del Chromium de Playwright
                    slow_mo=150,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-component-update",
                    ],
                    viewport={'width': 1280, 'height': 800},
                    locale="en-US",
                )
                
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    
                    # Aplicar Stealth mode para evadir detección básica de bots
                    from playwright_stealth import Stealth
                    await Stealth().apply_stealth_async(page)
                    await cls._emit_log(f"🥷 [CAITLYN] Modo Stealth activado para evadir anti-bots")
                    
                    # --- NAVEGAR ---
                    print(f"🌐 [CAITLYN] Abriendo portal: {target_url}")
                    try:
                        await page.goto(target_url, timeout=60000)
                        await page.wait_for_load_state("domcontentloaded", timeout=20000)
                    except Exception as e:
                        print(f"⚠️ [CAITLYN] La página tardó en cargar, continuando...")

                    # Esperamos un poco más para que JS/Web Components se rendericen
                    await asyncio.sleep(5)

                    
                    # --- LIMPIEZA DE BANNERS (COOKIES) ---
                    await cls._emit_log(f"🧹 [CAITLYN] Limpiando banners de cookies y modales...")
                    try:
                        # Buscamos botones de "Accept All", "Agree", "Allow all", "Select All"
                        cookies_btn = page.locator('button:has-text("Accept"), button:has-text("Agree"), button:has-text("Allow"), button:has-text("Select All"), button[id*="cookie-accept"]').first
                        if await cookies_btn.is_visible(timeout=5000):
                            await cookies_btn.click()
                            await cls._emit_log("✅ [CAITLYN] Cookies aceptadas")
                            await asyncio.sleep(2)
                    except:
                        pass
                        
                    # Presionar ESC para cerrar encuestas, "Ask Maersk" o popups molestos
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1)
                    await page.keyboard.press("Escape")

                    # --- EXTRAER TÉRMINOS DE BÚSQUEDA ---
                    usa_locode = sitio_soporta_locode(target_url)
                    origen_busqueda = extraer_busqueda(origen, usar_locode=usa_locode)
                    destino_busqueda = extraer_busqueda(destino, usar_locode=usa_locode)
                    
                    await cls._emit_log(f"🎯 [CAITLYN] [{site_name.upper()}] Buscando: '{origen_busqueda}' -> '{destino_busqueda}'")
                    
                    # --- NAVEGACIÓN INTELIGENTE (AGENTIC VISION) ---
                    await cls._emit_log(f"🧠 [CAITLYN] Escaneando interfaz visualmente con Gemini...")
                    
                    # Inyectar Set-of-Mark
                    await page.evaluate(SOM_JS)
                    await asyncio.sleep(1) # Esperar renderizado de etiquetas rojas
                    
                    som_screenshot = await page.screenshot(full_page=False) # Viewport es suficiente usualmente
                    
                    instrucciones = f"Busca el input para el puerto de origen, el de destino y el botón de búsqueda. Devuelve un JSON como {{\"origen\": 1, \"destino\": 2, \"buscar\": 3}}. Si no hay origen o destino, exclúyelos."
                    
                    try:
                        targets = await ScraperAIService.get_som_target(som_screenshot, instrucciones)
                        await cls._emit_log(f"🎯 [CAITLYN] Ojos de Gemini detectaron: {targets}")
                        
                        if "origen" in targets:
                            loc = page.locator(f"[data-som-id='{targets['origen']}']").first
                            if await loc.is_visible(timeout=2000):
                                await loc.click()
                                await loc.fill("")
                                await loc.press_sequentially(origen_busqueda, delay=100)
                                await asyncio.sleep(1)
                                await page.keyboard.press("Enter")
                                await asyncio.sleep(1)
                                
                        if "destino" in targets:
                            loc = page.locator(f"[data-som-id='{targets['destino']}']").first
                            if await loc.is_visible(timeout=2000):
                                await loc.click()
                                await loc.fill("")
                                await loc.press_sequentially(destino_busqueda, delay=100)
                                await asyncio.sleep(1)
                                await page.keyboard.press("Enter")
                                await asyncio.sleep(1)
                                
                        if "buscar" in targets:
                            loc = page.locator(f"[data-som-id='{targets['buscar']}']").first
                            if await loc.is_visible(timeout=2000):
                                await loc.click(force=True)
                                
                        await cls._emit_log(f"🎯 [CAITLYN] Acción disparada mediante IA Visual.")
                    except Exception as e:
                        await cls._emit_log(f"⚠️ [CAITLYN] Falló el agente visual: {e}")
                        # Fallback a ENTER
                        await page.keyboard.press("Enter")

                    # --- RESULTADOS Y CAPTURA ---
                    await cls._emit_log(f"⏳ [CAITLYN] Esperando resultados...")
                    await asyncio.sleep(8)
                    
                    screenshot_path = f"app/ai/{screenshot_name}"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"📸 [CAITLYN] Captura completada: {screenshot_path}")
                    
                    # --- EXTRACCIÓN CON COHERE ---
                    await cls._emit_log(f"🧠 [CAITLYN] Leyendo y extrayendo resultados con Cohere...")
                    # Limpiamos JS inyectado previamente (SOM) si es que interfiriera, aunque lo quitamos al recargar.
                    # Extraer el innerText es super rápido y limpio
                    try:
                        raw_html_text = await page.evaluate("document.body.innerText")
                        itineraries = await ScraperAIService.extract_schedules_json(raw_html_text)
                        await cls._emit_log(f"✅ [CAITLYN] Extracción perfecta: {len(itineraries)} itinerarios encontrados.")
                        return {"status": "success", "data": itineraries, "screenshot": screenshot_path}
                    except Exception as e:
                        await cls._emit_log(f"❌ [CAITLYN] Error de Cohere extrayendo texto: {e}")
                        return {"status": "error", "message": f"Fallo extracción: {e}", "screenshot": screenshot_path}

                finally:
                    await context.close()
        except Exception as e:
            print(f"❌ [CAITLYN] Error crítico en misión {target_url}: {e}")
            return {"status": "error", "message": str(e)}

# Para probarlo directamente
if __name__ == "__main__":
    asyncio.run(ScheduleHunterService.cazar_itinerarios("Miami, FL, USA", "Manzanillo, Panama"))
