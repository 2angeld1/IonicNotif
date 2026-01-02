from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import Trip, TripCreate
from app.services.trip_service import TripService
from app.services.ml_service import MLService

router = APIRouter(prefix="/trips", tags=["Viajes"])


@router.post("/", response_model=Trip)
async def save_trip(
    trip: TripCreate,
    weather_condition: str = None,
    temperature: float = None,
    had_incidents: bool = False
):
    """
    Registrar un viaje completado
    
    Estos datos se usan para entrenar el modelo ML
    """
    return await TripService.save_trip(
        trip=trip,
        weather_condition=weather_condition,
        temperature=temperature,
        had_incidents=had_incidents
    )


@router.get("/count")
async def get_trips_count():
    """Obtener cantidad de viajes registrados"""
    count = await TripService.get_trips_count()
    return {
        "count": count,
        "ready_for_training": count >= 10,
        "message": f"Tienes {count} viajes registrados. " + 
                  ("¡Puedes entrenar el modelo!" if count >= 10 else f"Necesitas {10 - count} más para entrenar.")
    }


@router.get("/")
async def get_trips(limit: int = 100):
    """Obtener viajes registrados"""
    trips = await TripService.get_all_trips(limit=limit)
    return {"trips": trips, "count": len(trips)}


@router.post("/train")
async def train_model():
    """
    Entrenar modelo ML con los viajes registrados
    
    Requiere al menos 10 viajes
    """
    trips = await TripService.get_all_trips(limit=5000)
    result = await MLService.train_model(trips)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/model-status")
async def get_model_status():
    """Obtener estado del modelo ML"""
    trips_count = await TripService.get_trips_count()
    
    return {
        "is_trained": MLService.is_trained,
        "trips_count": trips_count,
        "ready_for_training": trips_count >= 10,
        "using_heuristics": not MLService.is_trained,
        "message": "Modelo ML activo" if MLService.is_trained else "Usando heurísticas (entrena el modelo para mejores predicciones)"
    }
