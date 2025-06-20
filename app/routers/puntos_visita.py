from fastapi import APIRouter, HTTPException
from typing import List
from app.services.puntos_visita import obtener_puntos_visita_desde_db
from app.models.schemas import PuntoVisita

router = APIRouter()

@router.get("/puntos-visita", response_model=List[PuntoVisita])
def obtener_puntos_visita():
    """
    Devuelve la lista de puntos de visita disponibles en la base de datos.
    """
    try:
        return obtener_puntos_visita_desde_db()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener puntos de visita: {str(e)}")
