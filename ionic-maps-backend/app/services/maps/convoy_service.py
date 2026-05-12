from datetime import datetime, timedelta
import random
import string
import uuid
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.schemas import Convoy, ConvoyCreate, ConvoyJoin, ConvoyMember, ConvoyMemberStatus, LatLng

class ConvoyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.convoys

    def _generate_code(self, length=4) -> str:
        """Genera un código corto único (ej: AB12)"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    async def create_convoy(self, data: ConvoyCreate) -> Convoy:
        convoy_id = str(uuid.uuid4())
        host_id = str(uuid.uuid4()) # ID único para el creador
        code = self._generate_code()
        
        # Verificar que el código no exista (simple check)
        while await self.collection.find_one({"code": code, "is_active": True}):
            code = self._generate_code()
            
        host_member = ConvoyMember(
            user_id=host_id,
            name=data.host_name,
            location=data.start_location,
            last_update=datetime.utcnow(),
            status=ConvoyMemberStatus.ONLINE
        )
        
        convoy_doc = {
            "_id": convoy_id,
            "code": code,
            "host_id": host_id,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "members": [host_member.dict()]
        }
        
        await self.collection.insert_one(convoy_doc)
        return Convoy(**convoy_doc)

    async def join_convoy(self, data: ConvoyJoin) -> Optional[dict]:
        """Retorna {convoy: Convoy, user_id: str} o None si no existe"""
        convoy_doc = await self.collection.find_one({"code": data.convoy_code.upper(), "is_active": True})
        
        if not convoy_doc:
            return None
            
        new_user_id = str(uuid.uuid4())
        new_member = ConvoyMember(
            user_id=new_user_id,
            name=data.user_name,
            location=data.location,
            last_update=datetime.utcnow(),
            status=ConvoyMemberStatus.ONLINE
        )
        
        await self.collection.update_one(
            {"_id": convoy_doc["_id"]},
            {"$push": {"members": new_member.dict()}}
        )
        
        # Recargar para devolver estado actualizado
        updated_doc = await self.collection.find_one({"_id": convoy_doc["_id"]})
        return {
            "convoy": Convoy(**updated_doc),
            "user_id": new_user_id
        }

    async def update_member_location(self, convoy_id: str, user_id: str, location: LatLng) -> Optional[Convoy]:
        """Actualiza la ubicación de un miembro y retorna el convoy actualizado"""
        # Actualizar location y timestamp del miembro específico
        result = await self.collection.update_one(
            {"_id": convoy_id, "members.user_id": user_id},
            {
                "$set": {
                    "members.$.location": location.dict(),
                    "members.$.last_update": datetime.utcnow(),
                    "members.$.status": ConvoyMemberStatus.ONLINE
                }
            }
        )
        
        if result.modified_count == 0:
            return None
            
        # Opcional: Marcar como offline a miembros inactivos por > 5 min
        # Esto podría hacerse en un background task, pero por ahora lo dejamos simple
        
        updated_doc = await self.collection.find_one({"_id": convoy_id})
        return Convoy(**updated_doc)

    async def get_convoy(self, convoy_id: str) -> Optional[Convoy]:
        doc = await self.collection.find_one({"_id": convoy_id})
        if doc:
            return Convoy(**doc)
        return None
