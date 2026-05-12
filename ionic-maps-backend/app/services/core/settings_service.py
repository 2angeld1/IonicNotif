from app.database import get_database
from app.models.schemas import UserSettings, VoiceMode

class SettingsService:
    @staticmethod
    async def get_settings() -> UserSettings:
        db = get_database()
        # Buscar el unico documento de settings (singleton)
        settings_doc = await db.settings.find_one({})
        
        if not settings_doc:
            # Crear por defecto si no existe
            default_settings = UserSettings(voice_mode=VoiceMode.ALL)
            await db.settings.insert_one(default_settings.dict())
            return default_settings
        
        return UserSettings(**settings_doc)

    @staticmethod
    async def update_settings(settings: UserSettings) -> UserSettings:
        db = get_database()
        # Actualizar (upsert) el unico documento
        # Como no tenemos ID fijo, usamos find_one_and_update sobre el primero que encuentre o upsert
        # Pero mejor borrar cualquier otro y dejar solo uno, o simplemente actualizar el primero.
        # Estrategia: update_one con upsert=True en un query vacío {}
        
        await db.settings.update_one(
            {}, 
            {"$set": settings.dict()},
            upsert=True
        )
        
        return settings
