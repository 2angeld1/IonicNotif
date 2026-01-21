from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import (
    RouteRequest,
    RouteInfo,
    Incident
)
from app.services.routing_service import RoutingService
from app.services.weather_service import WeatherService
from app.services.incident_service import IncidentService
from app.services.ml_service import MLService

router = APIRouter(prefix="/routes", tags=["Rutas"])


@router.post("/calculate", response_model=RouteInfo)
async def calculate_route(request: RouteRequest):
    """
    Calcular ruta con predicción ML de tiempo
    
    Incluye:
    - Ruta óptima de OSRM
    - Predicción de tiempo ajustada por ML
    - Información del clima
    - Incidencias en la ruta
    """
    # Obtener ruta base de OSRM
    route_data = await RoutingService.get_route(request.start, request.end)
    
    if not route_data:
        raise HTTPException(status_code=404, detail="No se encontró ruta")
    
    route = route_data["routes"][0]
    base_duration = route["duration"]
    distance = route["distance"]
    coordinates = route["geometry"]["coordinates"]
    
    # Obtener clima
    weather = await WeatherService.get_weather(request.start.lat, request.start.lng)
    
    # Obtener incidencias en la ruta
    incidents = await IncidentService.get_incidents_on_route(coordinates)
    
    # Predecir tiempo con ML
    incident_severities = [inc.severity.value for inc in incidents]
    
    prediction = MLService.predict(
        base_duration=base_duration,
        distance=distance,
        weather_condition=weather.condition.value if weather else "clear",
        temperature=weather.temperature if weather else 25.0,
        incident_count=len(incidents),
        incident_severities=incident_severities
    )
    
    return RouteInfo(
        distance=distance,
        duration=base_duration,
        predicted_duration=prediction.predicted_duration,
        coordinates=coordinates,
        weather=weather,
        incidents_on_route=incidents,
        confidence=prediction.confidence,
        factors=prediction.factors_applied
    )


@router.post("/alternatives")
async def get_alternative_routes(request: RouteRequest):
    """
    Obtener rutas alternativas con predicciones
    """
    route_data = await RoutingService.get_route(request.start, request.end)
    
    if not route_data:
        raise HTTPException(status_code=404, detail="No se encontraron rutas")
    
    weather = await WeatherService.get_weather(request.start.lat, request.start.lng)
    
    alternatives = []
    
    for i, route in enumerate(route_data["routes"]):
        coordinates = route["geometry"]["coordinates"]
        base_duration = route["duration"]
        distance = route["distance"]
        
        # Incidencias para esta ruta específica
        incidents = await IncidentService.get_incidents_on_route(coordinates)
        incident_severities = [inc.severity.value for inc in incidents]
        
        prediction = MLService.predict(
            base_duration=base_duration,
            distance=distance,
            weather_condition=weather.condition.value if weather else "clear",
            temperature=weather.temperature if weather else 25.0,
            incident_count=len(incidents),
            incident_severities=incident_severities
        )
        
        alternatives.append({
            "index": i,
            "is_main": i == 0,
            "distance": distance,
            "duration": base_duration,
            "predicted_duration": prediction.predicted_duration,
            "coordinates": coordinates,
            "incidents_count": len(incidents),
            "confidence": prediction.confidence,
            "factors": prediction.factors_applied
        })
    
    # Ordenar por tiempo predicho
    alternatives.sort(key=lambda x: x["predicted_duration"])
    
    return {
        "weather": weather,
        "alternatives": alternatives,
        "recommended_index": alternatives[0]["index"] if alternatives else 0
    }


@router.post("/predict-external")
async def predict_external_routes(request: dict):
    """
    Aplicar predicciones ML a rutas externas (ej: de Google Maps)
    
    Recibe una lista de rutas con distance y duration, y devuelve
    predicciones ML para cada una, incluyendo confianza y factores.
    """
    routes = request.get("routes", [])
    start = request.get("start", {})
    
    if not routes:
        raise HTTPException(status_code=400, detail="No se proporcionaron rutas")
    
    # Obtener clima para la ubicación de inicio
    weather = None
    if start.get("lat") and start.get("lng"):
        weather = await WeatherService.get_weather(start["lat"], start["lng"])
    
    predictions = []
    
    for i, route in enumerate(routes):
        distance = route.get("distance", 0)
        duration = route.get("duration", 0)
        coordinates = route.get("coordinates", [])
        
        # Obtener incidencias en la ruta si hay coordenadas
        incidents = []
        if coordinates:
            try:
                incidents = await IncidentService.get_incidents_on_route(coordinates)
            except Exception:
                pass  # Si falla, continuamos sin incidencias
        
        incident_severities = [inc.severity.value for inc in incidents]
        
        # Predecir con ML
        prediction = MLService.predict(
            base_duration=duration,
            distance=distance,
            weather_condition=weather.condition.value if weather else "clear",
            temperature=weather.temperature if weather else 25.0,
            incident_count=len(incidents),
            incident_severities=incident_severities
        )
        
        predictions.append({
            "index": i,
            "original_duration": duration,
            "predicted_duration": prediction.predicted_duration,
            "confidence": prediction.confidence,
            "factors": prediction.factors_applied,
            "incidents_count": len(incidents),
            "time_saved": duration - prediction.predicted_duration if prediction.predicted_duration < duration else 0
        })
    
    # Ordenar por tiempo predicho para determinar recomendación
    sorted_predictions = sorted(predictions, key=lambda x: x["predicted_duration"])
    recommended_index = sorted_predictions[0]["index"] if sorted_predictions else 0
    
    return {
        "weather": weather,
        "predictions": predictions,
        "recommended_index": recommended_index
    }
