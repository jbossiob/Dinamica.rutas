from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.historial_rutas import obtener_historial_rutas_analista

router = APIRouter()

@router.get("/historial-rutas")
def obtener_historial_rutas(id_analista: int, db: Session = Depends(get_db)):
    """
    Devuelve el historial de rutas generadas para un analista, incluyendo los puntos de cada ruta.
    """
    try:
        resultado = obtener_historial_rutas_analista(db, id_analista)
        if not resultado:
            raise HTTPException(status_code=404, detail="No hay rutas asignadas para este analista")
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial de rutas: {str(e)}")
