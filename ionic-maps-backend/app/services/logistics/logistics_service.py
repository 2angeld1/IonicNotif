from app.scrapers.playwright_service import ScheduleHunterService
from app.services.core.socket_service import socket_manager
import os
import asyncio
import logging
import json
from datetime import datetime, timedelta
from app.database import get_database

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
    def _enrich_itinerary(cls, it: dict) -> dict:
        """Calcula métricas avanzadas (CO2 y Riesgo) usando matemáticas y heurísticas."""
        import re
        
        transshipments = str(it.get("transshipments", "")).lower()
        transit_time = str(it.get("transit_time", "")).lower()
        
        # Extraer días aproximados
        days_match = re.search(r'(\d+)', transit_time)
        days = int(days_match.group(1)) if days_match else 30
        
        # 1. Calcular Riesgo de Retraso
        if "direct" in transshipments or transshipments == "0":
            it["delay_risk"] = "Bajo (Directo)"
        elif "1" in transshipments:
            it["delay_risk"] = "Medio (1 Transbordo)"
        elif "2" in transshipments or "3" in transshipments:
            it["delay_risk"] = "Alto (Multi-Transbordo)"
        else:
            if days <= 15:
                it["delay_risk"] = "Bajo (Ruta Rápida)"
            elif days <= 35:
                it["delay_risk"] = "Medio"
            else:
                it["delay_risk"] = "Alto"
                
        # 2. Calcular Huella de Carbono (Si Cohere no la encontró en la web)
        if not it.get("co2_emissions"):
            # Aproximación matemática: 1 día de tránsito ~ 900 km. Factor emisión ~ 0.015 kg CO2 por TEU-km
            # CO2 (tons) = días * 900 * 0.015 / 1000 = días * 0.0135
            co2_tons = days * 0.0135
            
            # Penalidad por ineficiencias de transbordo (grúas, esperas)
            if "Medio" in it["delay_risk"]:
                co2_tons *= 1.2
            elif "Alto" in it["delay_risk"]:
                co2_tons *= 1.4
                
            it["co2_emissions"] = f"{co2_tons:.2f} Tons Est."
            
        return it

    @classmethod
    async def get_itineraries(cls, origin: str, destination: str, arrival_date: str = None):
        """
        Orquesta el flujo completo de búsqueda y extracción de datos.
        """
        msg = f"🚢 Caitlyn iniciando búsqueda logística MULTI-FUENTE: {origin} -> {destination}"
        logger.info(msg)
        await socket_manager.broadcast(msg)
        
        # --- 0. CACHÉ DE RUTAS COMPLETAS (Memoria Maestra) ---
        db = get_database()
        route_key = f"{origin.strip().lower()}|||{destination.strip().lower()}"
        
        # Buscar caché que no tenga más de 24 horas
        cached_route = await db.caitlyn_routes.find_one({"route_key": route_key})
        
        if cached_route:
            # Comprobar expiración (opcional, p.ej. 24 horas)
            fecha_cache = cached_route.get("created_at")
            if fecha_cache and (datetime.utcnow() - fecha_cache) < timedelta(hours=24):
                await socket_manager.broadcast(f"⚡ [CAITLYN] ¡Ruta '{origin}' a '{destination}' encontrada en Memoria Maestra! Sirviendo al instante.")
                return {
                    "success": True,
                    "origin": cached_route["origin"],
                    "destination": cached_route["destination"],
                    "itineraries": cached_route["itineraries"],
                    "message": f"¡Resultados instantáneos desde la memoria (Caché de {len(cached_route['itineraries'])} itinerarios)!"
                }
            else:
                await socket_manager.broadcast(f"🔄 [CAITLYN] La memoria de esta ruta caducó. Volviendo a cazar...")
        
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
                    # Añadimos la marca de la naviera y calculamos la analítica a cada registro
                    for it in source_itineraries:
                        it["source"] = source_name
                        it = cls._enrich_itinerary(it)
                    itineraries.extend(source_itineraries)
                    await socket_manager.broadcast(f"✅ [CAITLYN] {len(source_itineraries)} itinerarios analizados e integrados desde {source_name}")
                else:
                    logger.warning(f"⚠️ Misión {source_name} exitosa pero devolvió 0 itinerarios.")
                    
            elif res.get("status") == "error":
                logger.error(f"❌ Misión {mision['name']} reportó error: {res.get('message')}")

        if not itineraries:
            return {
                "success": False,
                "message": "Caitlyn no pudo extraer itinerarios de ninguna naviera."
            }

        # Guardar resultados exitosos en la Memoria Maestra (Caché de Ruta)
        await db.caitlyn_routes.update_one(
            {"route_key": route_key},
            {"$set": {
                "route_key": route_key,
                "origin": origin,
                "destination": destination,
                "itineraries": itineraries,
                "created_at": datetime.utcnow()
            }},
            upsert=True
        )

        return {
            "success": True,
            "origin": origin,
            "destination": destination,
            "itineraries": itineraries,
            "message": f"¡Caitlyn ha cazado {len(itineraries)} itinerarios en {len(misiones_activas)} fuentes!"
        }
