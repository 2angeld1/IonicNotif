from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()


class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    
db = Database()


async def connect_to_mongo():
    """Conectar a MongoDB"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    print(f"✅ Conectado a MongoDB: {settings.mongodb_url}")
    
    
async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if db.client:
        db.client.close()
        print("❌ Conexión a MongoDB cerrada")
        

def get_database():
    """Obtener instancia de la base de datos"""
    return db.client[settings.database_name]
