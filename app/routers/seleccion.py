from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SeleccionRequest
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.services.seleccion import registrar_puntos_visita_seleccionados

router = APIRouter()

@router.post("/seleccionar-puntos-visita")
def seleccionar_puntos_visita(data: SeleccionRequest, db: Session = Depends(get_db)):
    """
    Registra los puntos de visita seleccionados por un analista.
    """
    try:
        registrar_puntos_visita_seleccionados(db, data.id_analista, data.codigos_pc)
        return {"message": "Seleccion realizada correctamente"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al seleccionar puntos de visita: {str(e)}")







