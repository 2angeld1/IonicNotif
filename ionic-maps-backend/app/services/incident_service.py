from datetime import datetime, timedelta
from typing import List, Optional
from bson import ObjectId
from app.database import get_database
from app.models.schemas import (
    Incident, 
    IncidentCreate, 
    LatLng,
    IncidentType,
    IncidentSeverity
)


class IncidentService:
    """Servicio para manejar incidencias en rutas"""
    
    COLLECTION = "incidents"
    
    @classmethod
    async def create_incident(cls, incident: IncidentCreate) -> Incident:
        """Crear nueva incidencia"""
        db = get_database()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=incident.expires_in_minutes)
        
        doc = {
            "location": incident.location.model_dump(),
            "type": incident.type.value,
            "severity": incident.severity.value,
            "description": incident.description,
            "created_at": now,
            "expires_at": expires_at,
            "confirmations": 1,
            "is_active": True
        }
        
        result = await db[cls.COLLECTION].insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        
        return Incident(**doc)
    
    @classmethod
    async def get_active_incidents(
        cls,
        near_location: Optional[LatLng] = None,
        radius_km: float = 10.0
    ) -> List[Incident]:
        """Obtener incidencias activas"""
        db = get_database()
        
        query = {
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }
        
        # Si hay ubicación, filtrar por cercanía
        # (Para búsqueda geoespacial real, necesitarías índice 2dsphere)
        
        cursor = db[cls.COLLECTION].find(query).sort("created_at", -1)
        incidents = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            incident = Incident(**doc)
            
            if near_location:
                # Filtrar por distancia
                distance = cls._haversine(
                    near_location.lat, near_location.lng,
                    incident.location.lat, incident.location.lng
                )
                if distance <= radius_km:
                    incidents.append(incident)
            else:
                incidents.append(incident)
        
        return incidents
    
    @classmethod
    async def get_incidents_on_route(
        cls,
        route_coords: List[List[float]],
        threshold_km: float = 0.3
    ) -> List[Incident]:
        """Obtener incidencias que afectan una ruta específica"""
        db = get_database()
        
        query = {
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        }
        
        cursor = db[cls.COLLECTION].find(query)
        incidents_on_route = []
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            incident = Incident(**doc)
            
            # Verificar si la incidencia está cerca de algún punto de la ruta
            for coord in route_coords[::10]:  # Revisar cada 10 puntos para eficiencia
                lng, lat = coord[0], coord[1]
                distance = cls._haversine(
                    lat, lng,
                    incident.location.lat, incident.location.lng
                )
                if distance <= threshold_km:
                    incidents_on_route.append(incident)
                    break
        
        return incidents_on_route
    
    @classmethod
    async def confirm_incident(cls, incident_id: str) -> bool:
        """Confirmar una incidencia (otro usuario la vio)"""
        db = get_database()
        
        result = await db[cls.COLLECTION].update_one(
            {"_id": ObjectId(incident_id)},
            {
                "$inc": {"confirmations": 1},
                "$set": {
                    # Extender expiración si hay confirmaciones
                    "expires_at": datetime.utcnow() + timedelta(minutes=30)
                }
            }
        )
        return result.modified_count > 0
    
    @classmethod
    async def dismiss_incident(cls, incident_id: str) -> bool:
        """Marcar incidencia como resuelta"""
        db = get_database()
        
        result = await db[cls.COLLECTION].update_one(
            {"_id": ObjectId(incident_id)},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcular distancia entre dos puntos en km"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Radio de la Tierra en km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
