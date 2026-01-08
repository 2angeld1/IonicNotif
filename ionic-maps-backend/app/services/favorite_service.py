from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.database import get_database
from app.models.schemas import FavoritePlace, FavoritePlaceCreate, FavoriteType

class FavoriteService:
    @staticmethod
    async def add_favorite(favorite: FavoritePlaceCreate) -> dict:
        db = get_database()
        
        # Si es HOME o WORK, verificar si ya existe uno y actualizarlo
        if favorite.type in [FavoriteType.HOME, FavoriteType.WORK]:
            existing = await db.favorites.find_one({"type": favorite.type})
            if existing:
                await db.favorites.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {
                        "name": favorite.name,
                        "location": favorite.location.dict(),
                        "address": favorite.address,
                        "created_at": datetime.now()
                    }}
                )
                updated = await db.favorites.find_one({"_id": existing["_id"]})
                updated["_id"] = str(updated["_id"])
                return updated

        # Si no existe o es tipo FAVORITE/OTHER, crear nuevo
        new_favorite = favorite.dict()
        new_favorite["created_at"] = datetime.now()
        
        result = await db.favorites.insert_one(new_favorite)
        created = await db.favorites.find_one({"_id": result.inserted_id})
        if created:
            created["_id"] = str(created["_id"])
        return created

    @staticmethod
    async def get_favorites() -> List[dict]:
        db = get_database()
        cursor = db.favorites.find().sort("created_at", -1)
        favs = await cursor.to_list(length=100)
        for f in favs:
            f["_id"] = str(f["_id"])
        return favs

    @staticmethod
    async def delete_favorite(favorite_id: str) -> bool:
        db = get_database()
        result = await db.favorites.delete_one({"_id": ObjectId(favorite_id)})
        return result.deleted_count > 0

    @staticmethod
    async def get_by_id(favorite_id: str) -> Optional[dict]:
        db = get_database()
        return await db.favorites.find_one({"_id": ObjectId(favorite_id)})
