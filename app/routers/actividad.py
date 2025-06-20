from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import SeleccionActividadRequest
from app.db.database import get_db
from sqlalchemy.orm import Session
from app.services.actividad import registrar_actividades_seleccionadas

router = APIRouter()

@router.post("/seleccionar-actividades")
def seleccionar_actividades(data: SeleccionActividadRequest, db: Session = Depends(get_db)):
    """
    Registra las actividades seleccionadas por punto de visita para un analista.
    """
    try:
        registrar_actividades_seleccionadas(db, data.id_analista, data.actividades_por_punto)
        return {"message": "Actividades seleccionadas correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al seleccionar actividades: {str(e)}")