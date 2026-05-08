from app.scrapers.playwright_service import ScheduleHunterService
from app.scrapers.ocr_service import OCRService
from app.services.socket_service import socket_manager
import os
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

class LogisticsService:
    """
    Servicio de alto nivel para Muelle. 
    Coordina los scrapers y el procesamiento de IA local (OCR).
    """

    @classmethod
    def _load_config(cls):
        """Carga la configuración de navieras desde el JSON."""
        try:
            config_path = os.path.join(os.getcwd(), "app/ai/carriers.json")
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error cargando carriers.json: {e}")
            return []

    @classmethod
    async def get_itineraries(cls, origin: str, destination: str, arrival_date: str = None):
        """
        Orquesta el flujo completo de búsqueda y extracción de datos.
        """
        msg = f"🚢 Caitlyn iniciando búsqueda logística MULTI-FUENTE: {origin} -> {destination}"
        logger.info(msg)
        await socket_manager.broadcast(msg)
        
        # 1. Cargamos y filtramos las navieras activas
        misiones_activas = [m for m in cls._load_config() if m.get("active")]
        
        # Lanzamos las misiones en paralelo con red de seguridad
        tareas = [
            ScheduleHunterService.cazar_itinerarios(origin, destination, arrival_date, m["url"], m["file"])
            for m in misiones_activas
        ]
        hunter_results = await asyncio.gather(*tareas, return_exceptions=True)
        
        itineraries = []
        for i, res in enumerate(hunter_results):
            mision = misiones_activas[i]
            # Si res es una excepción o tiene status error, lo saltamos
            if isinstance(res, Exception):
                logger.error(f"❌ Error fatal en misión {mision['name']}: {res}")
                continue
                
            if res.get("status") == "success":
                source_name = mision["name"].upper()
                img_path = res.get("screenshot")
                
                try:
                    await socket_manager.broadcast(f"🔍 [OCR] Procesando resultados de {source_name}...")
                    raw_text = OCRService.extract_text_from_image(img_path)
                    # Procesamos este bloque de texto específico para esta fuente
                    source_itineraries = cls._parse_itineraries(raw_text, origin, destination, source_name)
                    itineraries.extend(source_itineraries)
                except Exception as e:
                    logger.error(f"❌ Error procesando OCR/Parsing para {source_name}: {e}")

        if not itineraries:
            return {
                "success": False,
                "message": "Caitlyn no pudo encontrar resultados legibles en ninguna de las fuentes."
            }

        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "itineraries": itineraries,
            "message": f"¡Caitlyn ha cazado {len(itineraries)} itinerarios en {len(misiones_activas)} fuentes diferentes!"
        }

    @classmethod
    def _parse_itineraries(cls, raw_text, origin, destination, source_name):
        """
        Parser interno que procesa una lista de textos y devuelve itinerarios etiquetados.
        """
        results = []
        navieras_conocidas = [
            "maersk", "msc", "cma", "hapag", "evergreen", "cosco", "ocean", 
            "yang ming", "one", "zim", "wan hai", "hyundai", "hmm", "pilot",
            "sealand", "hamburg", "arkas", "grimaldi", "safmarine"
        ]
        
        current_itinerary = {"source": source_name}
        
        for i, text in enumerate(raw_text):
            text_lower = text.lower()
            
            # Detectar Naviera
            if not current_itinerary.get("shipping_line"):
                for n in navieras_conocidas:
                    if n in text_lower:
                        current_itinerary["shipping_line"] = text
                        break
            
            # Detectar Precio
            if not current_itinerary.get("price"):
                if "$" in text or "usd" in text_lower:
                    current_itinerary["price"] = text
                elif text.replace(",","").replace(".","").isdigit() and len(text) >= 3:
                    if (i+1 < len(raw_text) and "usd" in raw_text[i+1].lower()) or \
                       (i-1 >= 0 and "usd" in raw_text[i-1].lower()):
                        current_itinerary["price"] = f"USD {text}"

            # Detectar Tiempo
            if not current_itinerary.get("transit_time"):
                if "day" in text_lower or "direct" in text_lower or "stop" in text_lower:
                    current_itinerary["transit_time"] = text
            
            # Cierre de Box
            if current_itinerary.get("shipping_line") and current_itinerary.get("price"):
                if current_itinerary.get("transit_time") or i == len(raw_text) - 1:
                    results.append(current_itinerary)
                    current_itinerary = {"source": source_name}
            
            # Reinicio por ciudad
            if origin.lower() in text_lower or destination.lower() in text_lower:
                if current_itinerary.get("shipping_line"):
                    results.append(current_itinerary)
                current_itinerary = {"source": source_name}

        return results
