from fastapi import APIRouter, HTTPException, Path
from typing import List
from app.models.schemas import FavoritePlace, FavoritePlaceCreate
from app.services.favorite_service import FavoriteService

router = APIRouter(
    prefix="/favorites",
    tags=["favorites"]
)

@router.get("/", response_model=List[FavoritePlace])
async def get_favorites():
    """Obtener todos los lugares favoritos"""
    return await FavoriteService.get_favorites()

@router.post("/", response_model=FavoritePlace)
async def add_favorite(favorite: FavoritePlaceCreate):
    """Guardar un nuevo lugar favorito"""
    return await FavoriteService.add_favorite(favorite)

@router.delete("/{id}")
async def delete_favorite(id: str = Path(..., title="ID del favorito")):
    """Eliminar un lugar favorito"""
    success = await FavoriteService.delete_favorite(id)
    if not success:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    return {"success": True, "message": "Lugar eliminado correctamente"}
