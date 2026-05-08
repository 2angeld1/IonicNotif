import asyncio
import os
import re
from playwright.async_api import async_playwright
from app.config import get_settings
from app.scrapers.smart_finder import SmartFinder
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
                    headless=True, 
                    slow_mo=150,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "--disable-component-update",
                    ],
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                    viewport={'width': 1280, 'height': 800},
                    locale="en-US",
                )
                
                try:
                    page = context.pages[0] if context.pages else await context.new_page()
                    
                    # --- NAVEGAR ---
                    print(f"🌐 [CAITLYN] Abriendo portal: {target_url}")
                    try:
                        await page.goto(target_url, timeout=60000)
                        await page.wait_for_load_state("domcontentloaded", timeout=20000)
                    except Exception as e:
                        print(f"⚠️ [CAITLYN] La página tardó en cargar, continuando...")

                    # Esperamos un poco más para que JS/Web Components se rendericen
                    await asyncio.sleep(5)

                    # --- SCREENSHOT DE DEBUG (para ver qué ve Caitlyn) ---
                    debug_path = f"app/ai/debug_{screenshot_name}"
                    await page.screenshot(path=debug_path, full_page=True)
                    
                    # --- LIMPIEZA DE BANNERS (COOKIES) ---
                    await cls._emit_log(f"🧹 [CAITLYN] Limpiando banners de cookies...")
                    try:
                        # Buscamos botones de "Accept All", "Agree", "Allow all"
                        cookies_btn = page.locator('button:has-text("Accept"), button:has-text("Agree"), button:has-text("Allow"), button[id*="cookie-accept"]').first
                        if await cookies_btn.is_visible(timeout=5000):
                            await cookies_btn.click()
                            await cls._emit_log("✅ [CAITLYN] Cookies aceptadas")
                            await asyncio.sleep(2)
                    except:
                        pass

                    # --- EXTRAER TÉRMINOS DE BÚSQUEDA ---
                    usa_locode = sitio_soporta_locode(target_url)
                    origen_busqueda = extraer_busqueda(origen, usar_locode=usa_locode)
                    destino_busqueda = extraer_busqueda(destino, usar_locode=usa_locode)
                    
                    await cls._emit_log(f"🎯 [CAITLYN] [{site_name.upper()}] Buscando: '{origen_busqueda}' -> '{destino_busqueda}'")
                    
                    # 1. Origen
                    origin_loc = await SmartFinder.find_origin(page)
                    origin_coords = None
                    if origin_loc:
                        box = await origin_loc.bounding_box()
                        if box: origin_coords = {"x": box['x'] + box['width']/2, "y": box['y'] + box['height']/2}
                    
                    if await SmartFinder.smart_fill(page, origin_loc, origen_busqueda):
                        await cls._emit_log(f"✅ [CAITLYN] Origen rellenado: {origen_busqueda}")
                        await asyncio.sleep(2) # Esperar a que salgan sugerencias
                        await page.keyboard.press("Enter") # Intentar seleccionar el primero
                        await asyncio.sleep(1)
                    else:
                        await cls._emit_log(f"❌ [CAITLYN] No se pudo rellenar el Origen")

                    # 2. Destino
                    dest_loc = await SmartFinder.find_destination(page, exclude_coords=origin_coords)
                    if await SmartFinder.smart_fill(page, dest_loc, destino_busqueda):
                        await cls._emit_log(f"✅ [CAITLYN] Destino rellenado: {destino_busqueda}")
                        await asyncio.sleep(2)
                        await page.keyboard.press("Enter")
                        await asyncio.sleep(1)
                    else:
                        await cls._emit_log(f"❌ [CAITLYN] No se pudo rellenar el Destino")

                    # 2.5 Fecha (ETA)
                    if arrival_date:
                        date_input = await SmartFinder.find_date_input(page)
                        if date_input:
                            # 🧠 DETECCIÓN DINÁMICA DE FORMATO
                            formato = await SmartFinder.detectar_formato_fecha(date_input)
                            fecha_formateada = arrival_date.replace("-", "/") # Default
                            
                            if formato:
                                y, m, d = arrival_date.split("-")
                                mapping = {"y": y, "m": m, "d": d}
                                try:
                                    fecha_formateada = formato["sep"].join([mapping[p] for p in formato["order"]])
                                    await cls._emit_log(f"🧠 [CAITLYN] Formato detectado dinámicamente: {fecha_formateada}")
                                except: pass
                            elif "msc" in target_url:
                                y, m, d = arrival_date.split("-")
                                fecha_formateada = f"{m}/{d}/{y}"

                            await cls._emit_log(f"⏳ [CAITLYN] Rellenando fecha con sigilo...")
                            try:
                                # Inyectar valor vía JS + disparar validaciones (input, change, blur)
                                await date_input.evaluate(f"(el, val) => {{ el.value = val; el.dispatchEvent(new Event('input', {{ bubbles: true }})); el.dispatchEvent(new Event('change', {{ bubbles: true }})); el.dispatchEvent(new Event('blur', {{ bubbles: true }})); }}", fecha_formateada)
                                await asyncio.sleep(1)
                                await cls._emit_log(f"✅ [CAITLYN] Fecha inyectada y validada: {fecha_formateada}")
                            except:
                                await SmartFinder.smart_fill(page, date_input, fecha_formateada)
                            
                            await page.keyboard.press("Enter")
                            await asyncio.sleep(1)

                    # 3. Buscar
                    search_btn = await SmartFinder.find_search_button(page)
                    if search_btn:
                        await cls._emit_log(f"🎯 [CAITLYN] Botón de búsqueda localizado, haciendo click...")
                        await search_btn.click(force=True)
                    else:
                        await cls._emit_log(f"⚠️ [CAITLYN] No se encontró el botón, usando ENTER de emergencia...")
                        await page.keyboard.press("Enter")
                    await cls._emit_log(f"🎯 [CAITLYN] Búsqueda disparada en {target_url}")

                    # --- RESULTADOS Y CAPTURA ---
                    await cls._emit_log(f"⏳ [CAITLYN] Esperando resultados...")
                    await asyncio.sleep(8)
                    
                    screenshot_path = f"app/ai/{screenshot_name}"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"📸 [CAITLYN] Captura completada: {screenshot_path}")
                    
                    return {"status": "success", "screenshot": screenshot_path}

                finally:
                    await context.close()

        except Exception as e:
            print(f"❌ [CAITLYN] Error crítico en misión {target_url}: {e}")
            return {"status": "error", "message": str(e)}

# Para probarlo directamente
if __name__ == "__main__":
    asyncio.run(ScheduleHunterService.cazar_itinerarios("Miami, FL, USA", "Manzanillo, Panama"))
