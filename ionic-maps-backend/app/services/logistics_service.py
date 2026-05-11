from app.scrapers.playwright_service import ScheduleHunterService
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
                source_itineraries = res.get("data", [])
                
                if source_itineraries:
                    # Añadimos la marca de la naviera a cada registro
                    for it in source_itineraries:
                        it["source"] = source_name
                    itineraries.extend(source_itineraries)
                    await socket_manager.broadcast(f"✅ [CAITLYN] {len(source_itineraries)} itinerarios integrados desde {source_name}")
                else:
                    logger.warning(f"⚠️ Misión {source_name} exitosa pero devolvió 0 itinerarios.")
                    
            elif res.get("status") == "error":
                logger.error(f"❌ Misión {mision['name']} reportó error: {res.get('message')}")

        if not itineraries:
            return {
                "success": False,
                "message": "Caitlyn no pudo extraer itinerarios de ninguna naviera."
            }

        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "itineraries": itineraries,
            "message": f"¡Caitlyn ha cazado {len(itineraries)} itinerarios en {len(misiones_activas)} fuentes!"
        }
