from app.models.models import SeleccionActividad
from app.services.exceptions import ErrorDeNegocio
from app.services.utils import validar_dict_no_vacio, validar_lista_no_vacia

def registrar_actividades_seleccionadas(db, id_analista, actividades_por_punto):
    """
    Borra las selecciones anteriores e inserta las nuevas actividades seleccionadas por punto para el analista.
    Lanza ErrorDeNegocio si los datos de entrada son inválidos.
    """
    try:
        validar_dict_no_vacio(actividades_por_punto, "actividades_por_punto")
        db.query(SeleccionActividad).filter_by(id_analista=id_analista).delete()
        for codigodece, actividades in actividades_por_punto.items():
            validar_lista_no_vacia(actividades, f"actividades para el punto {codigodece}")
            for actividad in actividades:
                seleccion = SeleccionActividad(
                    id_analista=id_analista,
                    codigodece=codigodece,
                    id_actividad=actividad
                )
                db.add(seleccion)
        db.commit()
        return True
    except ValueError as ve:
        raise ErrorDeNegocio(str(ve)) 