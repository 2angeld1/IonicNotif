import httpx
from typing import Optional
from app.config import get_settings
from app.models.schemas import WeatherInfo, WeatherCondition

settings = get_settings()


class WeatherService:
    """Servicio para obtener información del clima usando OpenWeatherMap"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    @staticmethod
    def _map_condition(weather_main: str) -> WeatherCondition:
        """Mapear condición de OpenWeatherMap a nuestro enum"""
        mapping = {
            "Clear": WeatherCondition.CLEAR,
            "Clouds": WeatherCondition.CLOUDS,
            "Rain": WeatherCondition.RAIN,
            "Drizzle": WeatherCondition.DRIZZLE,
            "Thunderstorm": WeatherCondition.THUNDERSTORM,
            "Snow": WeatherCondition.SNOW,
            "Mist": WeatherCondition.MIST,
            "Fog": WeatherCondition.FOG,
            "Haze": WeatherCondition.MIST,
            "Smoke": WeatherCondition.MIST,
        }
        return mapping.get(weather_main, WeatherCondition.CLEAR)
    
    @classmethod
    async def get_weather(cls, lat: float, lng: float) -> Optional[WeatherInfo]:
        """Obtener clima para una ubicación"""
        if not settings.openweather_api_key:
            # Si no hay API key, retornar clima por defecto
            return WeatherInfo(
                condition=WeatherCondition.CLEAR,
                temperature=28.0,
                humidity=70,
                visibility=10000,
                wind_speed=3.0,
                description="Clima no disponible (sin API key)"
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    cls.BASE_URL,
                    params={
                        "lat": lat,
                        "lon": lng,
                        "appid": settings.openweather_api_key,
                        "units": "metric",
                        "lang": "es"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                weather_main = data["weather"][0]["main"]
                
                return WeatherInfo(
                    condition=cls._map_condition(weather_main),
                    temperature=data["main"]["temp"],
                    humidity=data["main"]["humidity"],
                    visibility=data.get("visibility", 10000),
                    wind_speed=data["wind"]["speed"],
                    description=data["weather"][0]["description"]
                )
        except Exception as e:
            print(f"Error obteniendo clima: {e}")
            return WeatherInfo(
                condition=WeatherCondition.CLEAR,
                temperature=28.0,
                humidity=70,
                visibility=10000,
                wind_speed=3.0,
                description="Error obteniendo clima"
            )
