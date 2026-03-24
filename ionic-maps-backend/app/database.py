import sys
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
    print(f"✅ Conectado a MongoDB: {settings.mongodb_url}", file=sys.stderr)
    
    
async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if db.client:
        db.client.close()
        print("❌ Conexión a MongoDB cerrada", file=sys.stderr)
        

def get_database(name: Optional[str] = None):
    """
    Obtener instancia de una base de datos específica.
    Si no se pasa nombre, usa la de 'ionic_maps' por defecto (congelado por compatibilidad).
    """
    db_name = name if name else settings.database_name
    return db.client[db_name]
