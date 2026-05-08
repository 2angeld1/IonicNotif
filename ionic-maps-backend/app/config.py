from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = Field("mongodb://localhost:27017", validation_alias="MONGODB_URL")
    database_name: str = Field("ionic_maps", validation_alias="DATABASE_NAME")
    kitchy_database_name: str = Field("Kitchy", validation_alias="KITCHY_DATABASE_NAME")
    muelle_database_name: str = Field("muelle", validation_alias="MUELLE_DATABASE_NAME")
    
    # OpenWeatherMap
    openweather_api_key: str = Field("", validation_alias="OPENWEATHER_API_KEY")
    
    # OSRM
    osrm_base_url: str = Field("https://router.project-osrm.org", validation_alias="OSRM_BASE_URL")
    
    # Server
    host: str = Field("0.0.0.0", validation_alias="HOST")
    port: int = Field(8000, validation_alias="PORT")
    debug: bool = Field(True, validation_alias="DEBUG")
    
    # AI Services
    gemini_api_key: str = Field("", validation_alias="GEMINI_API_KEY")
    cohere_api_key: str = Field("", validation_alias="COHERE_API_KEY")
    
    # Scrapers Credentials
    searates_email: str = Field("", validation_alias="SEARATES_EMAIL")
    searates_password: str = Field("", validation_alias="SEARATES_PASSWORD")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

# --- CONFIGURACIÓN DE MODELOS DE IA (CASCADAS) ---
GEMINI_MODELS = [
    "gemini-2.5-flash-lite",         # Alta disponibilidad (Usar primero hoy)
    "gemini-2.5-flash",              # Estable
    "gemini-2.0-flash",              # Balanceado
    "gemini-2.0-flash-lite",         # El caballo de batalla
    "gemini-flash-latest",           
    "gemini-3.1-flash-lite-preview", 
]

COHERE_MODELS = [
    "command-r-plus-08-2024",        # Inteligencia superior para razonamiento
    "command-r-08-2024",             # El caballo de batalla para texto
    "command-r",                     # Versión base rápida
]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
