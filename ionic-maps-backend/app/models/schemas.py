from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============== UBICACIÓN ==============
class LatLng(BaseModel):
    lat: float
    lng: float


# ============== INCIDENCIAS ==============
class IncidentType(str, Enum):
    ACCIDENT = "accident"           # Accidente
    ROAD_WORK = "road_work"         # Trabajos en vía
    HAZARD = "hazard"               # Peligro general
    ANIMAL = "animal"               # Animal en vía
    POLICE = "police"               # Control policial
    FLOOD = "flood"                 # Inundación
    CLOSED_ROAD = "closed_road"     # Vía cerrada
    SLOW_TRAFFIC = "slow_traffic"   # Tráfico lento
    OTHER = "other"                 # Otro


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCreate(BaseModel):
    location: LatLng
    type: IncidentType
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    description: Optional[str] = None
    expires_in_minutes: int = 60  # Por defecto expira en 1 hora


class Incident(BaseModel):
    id: str = Field(alias="_id")
    location: LatLng
    type: IncidentType
    severity: IncidentSeverity
    description: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    confirmations: int = 0  # Usuarios que confirman la incidencia
    is_active: bool = True
    
    class Config:
        populate_by_name = True


# ============== CLIMA ==============
class WeatherCondition(str, Enum):
    CLEAR = "clear"
    CLOUDS = "clouds"
    RAIN = "rain"
    DRIZZLE = "drizzle"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    MIST = "mist"
    FOG = "fog"


class WeatherInfo(BaseModel):
    condition: WeatherCondition
    temperature: float  # Celsius
    humidity: int  # Porcentaje
    visibility: int  # Metros
    wind_speed: float  # m/s
    description: str


# ============== RUTAS ==============
class RouteRequest(BaseModel):
    start: LatLng
    end: LatLng
    start_name: Optional[str] = None
    end_name: Optional[str] = None


class RouteInfo(BaseModel):
    distance: float  # metros
    duration: float  # segundos (OSRM base)
    predicted_duration: float  # segundos (con ML)
    coordinates: List[List[float]]  # [lng, lat]
    weather: Optional[WeatherInfo] = None
    incidents_on_route: List[Incident] = []
    confidence: float = 0.0  # Confianza de la predicción (0-1)
    factors: dict = {}  # Factores que afectan el tiempo


# ============== VIAJES (para entrenar ML) ==============
class TripCreate(BaseModel):
    start: LatLng
    end: LatLng
    start_name: Optional[str] = None
    end_name: Optional[str] = None
    distance: float
    estimated_duration: float  # Lo que Google/OSRM predijo
    actual_duration: float     # Lo que realmente tardó (con tráfico)
    
    # Features para ML
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    hour: Optional[int] = None
    day_of_week: Optional[int] = None
    traffic_intensity: Optional[float] = 1.0
    had_incidents: bool = False
    incident_types: List[str] = []


class Trip(BaseModel):
    id: str = Field(alias="_id")
    start: LatLng
    end: LatLng
    start_name: Optional[str] = None
    end_name: Optional[str] = None
    distance: float
    estimated_duration: float
    actual_duration: float
    
    # Features para ML
    hour: int  # 0-23
    day_of_week: int  # 0=Lunes, 6=Domingo
    is_weekend: bool
    is_holiday: bool
    weather_condition: Optional[str] = None
    temperature: Optional[float] = None
    had_incidents: bool = False
    incident_types: List[str] = []
    
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ============== PREDICCIÓN ML ==============
class PredictionFeatures(BaseModel):
    distance: float
    hour: int
    day_of_week: int
    is_weekend: bool
    is_holiday: bool
    weather_condition: str = "clear"
    temperature: float = 25.0
    has_incidents: bool = False
    incident_count: int = 0


class PredictionResult(BaseModel):
    predicted_duration: float
    base_duration: float
    adjustment_factor: float
    confidence: float
    factors_applied: dict


# ============== LUGARES FAVORITOS ==============
class FavoriteType(str, Enum):
    HOME = "home"
    WORK = "work"
    FAVORITE = "favorite"
    OTHER = "other"


class FavoritePlaceCreate(BaseModel):
    name: str
    location: LatLng
    type: FavoriteType = FavoriteType.FAVORITE
    address: Optional[str] = None


class FavoritePlace(BaseModel):
    id: str = Field(alias="_id")
    name: str
    location: LatLng
    type: FavoriteType
    address: Optional[str] = None
    created_at: datetime
    
    class Config:
        populate_by_name = True


# ============== CONFIGURACIÓN DE USUARIO ==============
class VoiceMode(str, Enum):
    ALL = "all"
    ALERTS = "alerts"
    MUTE = "mute"


class UserSettings(BaseModel):
    voice_mode: VoiceMode = VoiceMode.ALL

