from app.models.models import RutasGeneradas, HistorialRuta
from app.services.exceptions import ErrorDeNegocio
from app.services.utils import validar_entero_positivo

def obtener_historial_rutas_analista(db, id_analista):
    """
    Devuelve el historial de rutas generadas para un analista, incluyendo los puntos de cada ruta.
    Lanza ErrorDeNegocio si el id_analista es inválido.
    """
    try:
        validar_entero_positivo(id_analista, "id_analista")
        rutas = (
            db.query(RutasGeneradas)
            .filter(RutasGeneradas.id_analista == id_analista)
            .order_by(RutasGeneradas.fecha_generacion.desc())
            .all()
        )
        if not rutas:
            return []
        resultado = []
        for ruta in rutas:
            puntos = (
                db.query(HistorialRuta)
                .filter(HistorialRuta.id_ruta == ruta.id)
                .order_by(HistorialRuta.dia_ruta, HistorialRuta.orden_visita)
                .all()
            )
            resultado.append({
                "id": ruta.id,
                "fecha_generacion": ruta.fecha_generacion.isoformat(),
                "duracion_total_min": ruta.duracion_total_min,
                "distancia_total_km": ruta.distancia_total_km,
                "prioridad_total": ruta.prioridad_total,
                "puntos": [
                    {
                        "codigodece": p.codigodece,
                        "orden_visita": p.orden_visita,
                        "dia_ruta": p.dia_ruta,
                        "prioridad": p.prioridad,
                        "tiempo_estimado_min": p.tiempo_estimado_min,
                        "distancia_km": p.distancia_km
                    }
                    for p in puntos
                ]
            })
        return resultado
    except ValueError as ve:
        raise ErrorDeNegocio(str(ve)) 