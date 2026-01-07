from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = Field("mongodb://localhost:27017", validation_alias="MONGODB_URL")
    database_name: str = Field("ionic_maps", validation_alias="DATABASE_NAME")
    
    # OpenWeatherMap
    openweather_api_key: str = Field("", validation_alias="OPENWEATHER_API_KEY")
    
    # OSRM
    osrm_base_url: str = Field("https://router.project-osrm.org", validation_alias="OSRM_BASE_URL")
    
    # Server
    host: str = Field("0.0.0.0", validation_alias="HOST")
    port: int = Field(8000, validation_alias="PORT")
    debug: bool = Field(True, validation_alias="DEBUG")
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
