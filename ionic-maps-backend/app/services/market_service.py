
import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from typing import Optional
from app.services.invoice_service import InvoiceService
from app.services.web_search_service import WebSearchService
from app.config import get_settings, GEMINI_MODELS
from app.database import get_database

class MarketService:
    """Servicio para que Caitlyn analice capturas de pantalla de mercados y combustible."""
    
    _client = None

    @classmethod
    def get_system_prompt(cls, tipo: str) -> str:
        """Genera un prompt de sistema específico para el tipo de mercado."""
        base = (
            "Eres Caitlyn, la experta en mercado de Kitchy en Panamá. "
            f"Analizarás información sobre {tipo}. "
            "Tu objetivo es extraer los precios actuales de forma precisa. "
            "Responde ÚNICAMENTE con un objeto JSON válido. "
            "Si no encuentras un dato, usa null.\n\n"
        )
        
        if tipo == 'FUEL':
            rules = (
                "REGLAS: Busca precios de Octano 95, 91 y Diesel (precio por litro). "
                "Busca palabras como 'Precios Máximos', '95 Octanos', 'Diesel'. "
                "Formato: { \"octane95\": number, \"octane91\": number, \"diesel\": number, \"fuente\": \"URL completa de la web donde viste los datos\" }"
            )
        elif tipo == 'MERCA':
            rules = (
                "REGLAS: Busca precios de vegetales y frutas (cebolla, papa, tomate, etc.). "
                "Formato: { \"productos\": [ { \"nombre\": string, \"precio\": number, \"unidad\": string } ], \"fuente\": \"URL completa de la web donde viste los datos\" }"
            )
        else: # ACODECO
            rules = (
                "REGLAS: Busca el costo de la canasta básica. "
                "Formato: { \"costo_total\": number, \"sector\": \"string\", \"fuente\": \"URL completa de la web donde viste los datos\" }"
            )
            
        return base + rules

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            settings = get_settings()
            cls._client = genai.Client(api_key=settings.gemini_api_key)
        return cls._client

    @classmethod
    async def parse_market_image(cls, tipo: str, image_base64: Optional[str] = None) -> dict:
        """
        Caitlyn analiza el mercado. 
        Primero mira el caché, luego intenta un Flashazo directo (Scraper), 
        luego Google Search y finalmente DuckDuckGo.
        """
        try:
            # --- 0. LÓGICA DE CACHÉ (Ahorro de API) ---
            if not image_base64:
                try:
                    db = get_database(get_settings().kitchy_database_name)
                    hace_12_horas = datetime.now().timestamp() - (12 * 3600)
                    
                    cache_entry = await db["marketcontexts"].find_one(
                        {"tipo": tipo, "timestamp": {"$gt": hace_12_horas}},
                        sort=[("timestamp", -1)]
                    )
                    
                    if cache_entry:
                        print(f"📦 [CACHE] Recuperados datos de {tipo} desde MongoDB.")
                        return {
                            "success": True,
                            "data": cache_entry.get("data"),
                            "metodo": "cache_mongodb",
                            "timestamp": cache_entry.get("timestamp")
                        }
                except Exception as e:
                    print(f"⚠️ [CACHE] Error consultando caché: {e}")

            client = cls._get_client()
            system_instruction = cls.get_system_prompt(tipo)
            last_error = "Error desconocido"

            # --- 1. MODO VISIÓN (Imagen) ---
            if image_base64:
                print(f"👁️ Caitlyn analizando imagen de {tipo}...")
                image_bytes, mime_type = InvoiceService._parse_base64_image(image_base64)
                prompt = f"Analiza esta captura de pantalla de {tipo} y extrae los precios actuales de mercado en Panamá."
                
                for model_name in GEMINI_MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json"
                            )
                        )
                        data = json.loads(response.text)
                        return {"success": True, "data": data, "metodo": f"gemini_vision_{model_name}"}
                    except Exception as model_err:
                        last_error = str(model_err)
                        print(f"⚠️ Modelo {model_name} falló para {tipo}: {model_err}")
                        continue
                
                # OCR Fallback
                try:
                    from app.services.caitlyn_vision_service import CaitlynVisionService
                    ocr_result = await CaitlynVisionService.blind_scan_invoice(image_base64)
                    return {"success": True, "data": ocr_result.get("productos", []), "metodo": "local_ocr_fallback"}
                except: pass

            # --- 2. MODO AGENTE (Investigación con Aprendizaje) ---
            else:
                # 🎯 PASO A: Intentar con FUENTES DIRECTAS (Memoria + Oficiales)
                print(f"🧠 Caitlyn consultando fuentes directas para {tipo}...")
                try:
                    db = get_database(get_settings().kitchy_database_name)
                    source_doc = await db["market_sources"].find_one({"tipo": tipo})
                    
                    from app.services.direct_scraper_service import DirectScraperService
                    
                    # Consolidamos URLs: las aprendidas + la oficial por defecto
                    candidate_urls = source_doc.get("urls", []) if source_doc else []
                    default_url = DirectScraperService.SOURCES.get(tipo)
                    if default_url and default_url not in candidate_urls:
                        candidate_urls.append(default_url)

                    for url in candidate_urls:
                        print(f"📸 Flashazo a: {url}")
                        scraper_result = DirectScraperService.get_page_content(tipo) if url == default_url else {"text": DirectScraperService.fetch_custom_url(url), "pdf_links": []}
                        
                        if scraper_result:
                            raw_web_content = scraper_result.get("text", "")
                            pdf_links = scraper_result.get("pdf_links", [])
                            
                            pdf_bytes = None
                            best_pdf_link = None
                            if pdf_links:
                                try:
                                    print(f"📄 Se encontraron PDFs. Caitlyn eligiendo el mejor...")
                                    month_names_es = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                                    now = datetime.now()
                                    current_month = month_names_es[now.month-1]
                                    current_year = now.strftime("%Y")
                                    
                                    selection_prompt = (
                                        f"Hoy es {current_month} de {current_year}.\n"
                                        f"En {url} encontré estos links a PDFs:\n{json.dumps(pdf_links)}\n\n"
                                        "¿Cuál es el link del PDF más reciente con precios? "
                                        f"Prioriza {current_month} {current_year}. Si no existe, elige el más cercano anterior. "
                                        "Responde solo la URL o 'null'."
                                    )
                                    sel_resp = client.models.generate_content(model=GEMINI_MODELS[0], contents=selection_prompt)
                                    best_pdf_link = sel_resp.text.strip()
                                    # Si lo que devolvió Gemini no parece una URL, forzamos error para ir al fallback
                                    if "http" not in best_pdf_link and not best_pdf_link.startswith('/'):
                                        raise ValueError("Respuesta de Gemini no es una URL")
                                except:
                                    # Fallback local: elegir el primer link razonable
                                    print("⚠️ Gemini no pudo elegir un link válido. Usando lógica local...")
                                    # Palabras clave de prioridad (mes actual y anterior)
                                    month_names = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
                                    now = datetime.now()
                                    target_months = [month_names[now.month-1].lower(), month_names[now.month-2].lower()]
                                    
                                    for link in pdf_links:
                                        link_low = link.lower()
                                        # Si coincide el mes actual o anterior Y tiene palabras clave de precios
                                        if any(m in link_low for m in target_months) and \
                                           any(x in link_low for x in ['precio', 'combustible', 'canasta', 'cba']):
                                            best_pdf_link = link
                                            print(f"🎯 Caitlyn eligió localmente (Prioridad Fecha): {best_pdf_link}")
                                            break
                                    
                                    # Si aún no hay nada, el primer link de precios que encuentre
                                    if not best_pdf_link:
                                        for link in pdf_links:
                                            if any(x in link.lower() for x in ['precio', 'combustible', 'canasta', 'cba']):
                                                best_pdf_link = link
                                                break
                            
                            if best_pdf_link and ("http" in best_pdf_link or best_pdf_link.startswith('/')):
                                # Asegurar URL completa si Gemini devolvió una relativa
                                if best_pdf_link.startswith('/'):
                                    best_pdf_link = "https://www.acodeco.gob.pa" + best_pdf_link
                                    
                                pdf_bytes = DirectScraperService.download_file(best_pdf_link)
                                if pdf_bytes:
                                    try:
                                        print(f"🤖 Caitlyn intentando leer PDF con Gemini ({len(pdf_bytes)} bytes)...")
                                        response = client.models.generate_content(
                                            model=GEMINI_MODELS[0],
                                            contents=[
                                                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                                                f"Extrae los precios de {tipo} para Panamá hoy. Responde solo JSON."
                                            ]
                                        )
                                        data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])
                                        if any(data.values()):
                                            await cls.learn_source(tipo, [best_pdf_link])
                                            await cls.save_to_cache(tipo, data)
                                            return {"success": True, "data": data, "metodo": "direct_flash_pdf_gemini"}
                                    except Exception as gemini_err:
                                        print(f"⚠️ Falló lectura de PDF con Gemini: {gemini_err}. Usando MODO SUPERVIVENCIA...")
                                        local_text = DirectScraperService.extract_text_from_pdf(pdf_bytes)
                                        from app.services.caitlyn_vision_service import CaitlynVisionService
                                        local_items = CaitlynVisionService._extract_products_from_text(local_text)
                                        if local_items:
                                            market_data = {item['nombre']: item['precioUnitario'] for item in local_items}
                                            await cls.learn_source(tipo, [best_pdf_link])
                                            await cls.save_to_cache(tipo, market_data)
                                            return {"success": True, "data": market_data, "metodo": "direct_flash_pdf_local_ocr"}
                            
                            # Si no hay PDF o falló el procesamiento PDF, intentar con el texto de la web
                            if raw_web_content:
                                try:
                                    response = client.models.generate_content(
                                        model=GEMINI_MODELS[0],
                                        contents=f"Extrae precios de {tipo} de este texto:\n\n{raw_web_content[:8000]}\n\n{system_instruction}"
                                    )
                                    data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])
                                    if any(data.values()):
                                        await cls.save_to_cache(tipo, data)
                                        return {"success": True, "data": data, "metodo": "direct_scraper_flashazo"}
                                except:
                                    pass
                except Exception as e:
                    print(f"⚠️ Error en fuentes directas: {e}")

                # 🎯 PASO B: Búsqueda en Google (Aprender nueva fuente)
                print(f"🔎 Caitlyn investigando nuevas fuentes para {tipo}...")
                search_query = f"precios actuales de {tipo} en Panama hoy"
                
                for model_name in GEMINI_MODELS:
                    try:
                        print(f"🤖 Investigando con {model_name}...")
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=search_query,
                                config=types.GenerateContentConfig(
                                    system_instruction=system_instruction,
                                    tools=[types.Tool(google_search=types.GoogleSearch())],
                                )
                            )
                        except Exception as e:
                            last_error = str(e)
                            print(f"⚠️ Error en {model_name}: {last_error}")
                            continue # Probamos el siguiente modelo
                        
                        data = json.loads(response.text[response.text.find('{'):response.text.rfind('}')+1])
                        
                        # --- 🎓 EL APRENDIZAJE: Extraer URLs del Grounding ---
                        new_urls = []
                        try:
                            if data.get("fuente") and (data["fuente"].startswith("http")) and ("google.com" not in data["fuente"]):
                                new_urls.append(data["fuente"])
                            
                            metadata = response.candidates[0].grounding_metadata
                            if metadata and metadata.grounding_chunks:
                                for chunk in metadata.grounding_chunks:
                                    if chunk.web and chunk.web.uri and ("google.com" not in chunk.web.uri):
                                        new_urls.append(chunk.web.uri)
                        except: pass
                        
                        if new_urls: await cls.learn_source(tipo, new_urls)
                        await cls.save_to_cache(tipo, data)
                        return {"success": True, "data": data, "metodo": f"google_search_learned_{model_name}"}
                    
                    except Exception as e:
                        print(f"⚠️ Falló procesamiento en {model_name}: {e}")
                        continue

                # --- PASO C: Fallback a DuckDuckGo ---
                print(f"🦆 [FALLBACK] Google falló. Usando DuckDuckGo para {tipo}...")
                simple_query = f"precios {tipo} Panama hoy"
                web_results = WebSearchService.search_panama_prices(simple_query)
                if web_results:
                    try:
                        response = client.models.generate_content(
                            model=GEMINI_MODELS[0],
                            contents=(
                                f"Resultados de DuckDuckGo sobre {tipo}:\n{json.dumps(web_results)}\n\n"
                                f"{system_instruction}\nExtrae el JSON."
                            )
                        )
                        raw_text = response.text
                        data = json.loads(raw_text[raw_text.find('{'):raw_text.rfind('}')+1])
                        await cls.save_to_cache(tipo, data)
                        return {"success": True, "data": data, "metodo": "duckduckgo_fallback_parsed"}
                    except Exception as e:
                        print(f"❌ Falló el parseo del fallback: {e}")

            return {"success": False, "error": f"Caitlyn no pudo encontrar datos de {tipo}.", "detalle": last_error}

        except Exception as e:
            print(f"❌ Error fatal en MarketService: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def learn_source(cls, tipo: str, urls: list):
        """Guarda una URL exitosa en la base de datos de fuentes aprendidas."""
        try:
            db = get_database(get_settings().kitchy_database_name)
            await db["market_sources"].update_one(
                {"tipo": tipo},
                {"$addToSet": {"urls": {"$each": urls}}},
                upsert=True
            )
            print(f"🎓 [APRENDIZAJE] Caitlyn memorizó nuevas fuentes para {tipo}: {urls}")
        except Exception as e:
            print(f"⚠️ [APRENDIZAJE] No se pudo memorizar la fuente: {e}")

    @classmethod
    async def save_to_cache(cls, tipo: str, data: dict):
        """Guarda los resultados en MongoDB."""
        try:
            db = get_database(get_settings().kitchy_database_name)
            await db["marketcontexts"].update_one(
                {"tipo": tipo},
                {
                    "$set": {
                        "data": data,
                        "timestamp": datetime.now().timestamp(),
                        "fecha": datetime.now()
                    }
                },
                upsert=True
            )
            print(f"💾 [CACHE] Datos de {tipo} guardados en MongoDB.")
        except Exception as e:
            print(f"⚠️ [CACHE] No se pudo guardar: {e}")
