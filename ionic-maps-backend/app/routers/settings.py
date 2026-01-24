from fastapi import APIRouter
from app.models.schemas import UserSettings
from app.services.settings_service import SettingsService

router = APIRouter(
    prefix="/settings",
    tags=["settings"]
)

@router.get("/", response_model=UserSettings)
async def get_settings():
    """Obtener configuración de usuario"""
    return await SettingsService.get_settings()

@router.post("/", response_model=UserSettings)
async def update_settings(settings: UserSettings):
    """Actualizar configuración de usuario"""
    return await SettingsService.update_settings(settings)
