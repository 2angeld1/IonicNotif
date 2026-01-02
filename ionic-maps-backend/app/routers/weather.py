from fastapi import APIRouter
from app.models.schemas import WeatherInfo
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["Clima"])


@router.get("/", response_model=WeatherInfo)
async def get_weather(lat: float, lng: float):
    """Obtener información del clima para una ubicación"""
    return await WeatherService.get_weather(lat, lng)
