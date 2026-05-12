from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.schemas import (
    Incident,
    IncidentCreate,
    LatLng,
    IncidentType
)
from app.services.maps.incident_service import IncidentService

router = APIRouter(prefix="/incidents", tags=["Incidencias"])


@router.post("/", response_model=Incident)
async def create_incident(incident: IncidentCreate):
    """
    Reportar una nueva incidencia
    
    Tipos disponibles:
    - accident: Accidente
    - road_work: Trabajos en vía
    - hazard: Peligro general
    - animal: Animal en vía
    - police: Control policial
    - flood: Inundación
    - closed_road: Vía cerrada
    - slow_traffic: Tráfico lento
    - other: Otro
    """
    return await IncidentService.create_incident(incident)


@router.get("/", response_model=List[Incident])
async def get_incidents(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: float = 10.0
):
    """
    Obtener incidencias activas
    
    Si se proporcionan lat/lng, filtra por cercanía
    """
    near_location = None
    if lat is not None and lng is not None:
        near_location = LatLng(lat=lat, lng=lng)
    
    return await IncidentService.get_active_incidents(
        near_location=near_location,
        radius_km=radius_km
    )


@router.get("/types")
async def get_incident_types():
    """Obtener tipos de incidencias disponibles"""
    return {
        "types": [
            {"value": "accident", "label": "🚗 Accidente", "icon": "car-crash"},
            {"value": "road_work", "label": "🚧 Trabajos en vía", "icon": "construct"},
            {"value": "hazard", "label": "⚠️ Peligro", "icon": "warning"},
            {"value": "animal", "label": "🐕 Animal en vía", "icon": "paw"},
            {"value": "police", "label": "👮 Control policial", "icon": "shield"},
            {"value": "flood", "label": "🌊 Inundación", "icon": "water"},
            {"value": "closed_road", "label": "🚫 Vía cerrada", "icon": "close-circle"},
            {"value": "slow_traffic", "label": "🐌 Tráfico lento", "icon": "speedometer"},
            {"value": "other", "label": "📍 Otro", "icon": "location"},
        ]
    }


@router.post("/{incident_id}/confirm")
async def confirm_incident(incident_id: str):
    """Confirmar que la incidencia sigue activa"""
    success = await IncidentService.confirm_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return {"message": "Incidencia confirmada"}


@router.post("/{incident_id}/dismiss")
async def dismiss_incident(incident_id: str):
    """Marcar incidencia como resuelta"""
    success = await IncidentService.dismiss_incident(incident_id)
    if not success:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    return {"message": "Incidencia marcada como resuelta"}
