from datetime import datetime
from typing import List, Optional
import hashlib
from bson import ObjectId
from app.database import get_database
from app.models.schemas import Trip, TripCreate, LatLng
from app.utils.holidays import is_holiday_from_datetime


class TripService:
    """Servicio para manejar viajes registrados (datos de entrenamiento)"""
    
    COLLECTION = "trips"
    
    @classmethod
    async def save_trip(cls, trip: TripCreate) -> Trip:
        """Guardar un viaje completado"""
        db = get_database()
        
        now = datetime.utcnow()
        hour = trip.hour if trip.hour is not None else now.hour
        day_of_week = trip.day_of_week if trip.day_of_week is not None else now.weekday()
        
        # Generar hash de ruta para identificar rutas frecuentes
        route_key = f"{trip.start.lat:.4f},{trip.start.lng:.4f}-{trip.end.lat:.4f},{trip.end.lng:.4f}"
        route_hash = hashlib.md5(route_key.encode()).hexdigest()[:12]
        
        doc = {
            "start": trip.start.model_dump(),
            "end": trip.end.model_dump(),
            "start_name": trip.start_name,
            "end_name": trip.end_name,
            "distance": trip.distance,
            "estimated_duration": trip.estimated_duration,
            "actual_duration": trip.actual_duration,
            
            # Features para ML
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": day_of_week >= 5,
            "is_holiday": is_holiday_from_datetime(now),
            "weather_condition": trip.weather_condition,
            "temperature": trip.temperature,
            "traffic_intensity": trip.traffic_intensity or (trip.actual_duration / trip.estimated_duration if trip.estimated_duration > 0 else 1.0),
            "had_incidents": trip.had_incidents,
            "incident_types": trip.incident_types,
            
            # Historial personal
            "route_hash": route_hash,
            
            "created_at": now
        }
        
        result = await db[cls.COLLECTION].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        
        return Trip(**doc)
    
    @classmethod
    async def get_all_trips(cls, limit: int = 1000) -> List[dict]:
        """Obtener todos los viajes para entrenamiento"""
        db = get_database()
        
        cursor = db[cls.COLLECTION].find().sort("created_at", -1).limit(limit)
        trips = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            trips.append(doc)
        
        return trips
    
    @classmethod
    async def get_trips_count(cls) -> int:
        """Obtener cantidad de viajes registrados"""
        db = get_database()
        return await db[cls.COLLECTION].count_documents({})
    
    @classmethod
    async def get_similar_trips(
        cls,
        start: LatLng,
        end: LatLng,
        radius_km: float = 1.0,
        limit: int = 50
    ) -> List[dict]:
        """Obtener viajes similares para predicción contextual"""
        db = get_database()
        
        # Por simplicidad, buscar todos y filtrar
        # En producción, usar índices geoespaciales
        cursor = db[cls.COLLECTION].find().limit(500)
        similar = []
        
        async for doc in cursor:
            # Verificar si origen y destino están cerca
            start_dist = cls._haversine(
                start.lat, start.lng,
                doc["start"]["lat"], doc["start"]["lng"]
            )
            end_dist = cls._haversine(
                end.lat, end.lng,
                doc["end"]["lat"], doc["end"]["lng"]
            )
            
            if start_dist <= radius_km and end_dist <= radius_km:
                doc["_id"] = str(doc["_id"])
                similar.append(doc)
                
                if len(similar) >= limit:
                    break
        
        return similar
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distancia entre dos puntos en km"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
