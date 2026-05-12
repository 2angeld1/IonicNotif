import sys
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()


class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    
db = Database()


async def connect_to_mongo():
    """Conectar a MongoDB con timeout para evitar bloqueos"""
    try:
        # Añadimos un timeout corto (2 segundos) para que no se quede colgado
        db.client = AsyncIOMotorClient(
            settings.mongodb_url, 
            serverSelectionTimeoutMS=2000
        )
        # Intentamos una operación rápida para verificar la conexión
        await db.client.admin.command('ping')
        print(f"✅ Conectado a MongoDB: {settings.mongodb_url}", file=sys.stderr)
    except Exception as e:
        db.client = None
        print(f"⚠️ MODO OFFLINE: No se pudo conectar a MongoDB ({e})", file=sys.stderr)
        print("💡 La app seguirá funcionando pero sin persistencia en DB.", file=sys.stderr)

    
    
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
