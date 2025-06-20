from app.models.models import SeleccionPC
from datetime import datetime
from app.services.exceptions import ErrorDeNegocio
from app.services.utils import validar_lista_no_vacia

def registrar_puntos_visita_seleccionados(db, id_analista, codigos_pc):
    """
    Borra las selecciones anteriores e inserta los nuevos puntos de visita seleccionados por el analista.
    Lanza ErrorDeNegocio si los datos de entrada son inválidos.
    """
    try:
        validar_lista_no_vacia(codigos_pc, "lista de puntos de visita")
        if len(codigos_pc) < 3:
            raise ValueError("Debes seleccionar como minimo 3 puntos de visita")
        db.query(SeleccionPC).filter_by(id_analista=id_analista).delete()
        fecha_comun = datetime.now()
        for codigodece in codigos_pc:
            seleccion = SeleccionPC(
                id_analista=id_analista,
                codigodece=codigodece,
                fecha_seleccion=fecha_comun
            )
            db.add(seleccion)
        db.commit()
        return True
    except ValueError as ve:
        raise ErrorDeNegocio(str(ve)) 