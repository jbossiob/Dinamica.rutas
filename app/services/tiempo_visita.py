from typing import List, Dict
from app.models.schemas import PuntoVisita
from sqlalchemy.orm import Session
from app.models.models import SeleccionActividad, Actividad
import requests
import os
from app.services.exceptions import ErrorDeNegocio

def obtener_tiempo_por_punto(db: Session, id_analista: int) -> Dict[str, List[int]]:
    """
    Devuelve un diccionario con los tiempos de actividades por punto para un analista.
    Lanza ErrorDeNegocio si no se encuentran resultados.
    """
    resultados = (
        db.query(SeleccionActividad.codigodece, Actividad.duracion_min)
        .join(Actividad, SeleccionActividad.id_actividad == Actividad.id)
        .filter(SeleccionActividad.id_analista == id_analista)
        .all()
    )
    if resultados is None:
        raise ErrorDeNegocio("No se encontraron actividades para el analista proporcionado.")
    tiempo_por_punto = {}
    for codigodece, tiempo in resultados:
        tiempo_por_punto.setdefault(codigodece, []).append(tiempo)
    return tiempo_por_punto

def distribuir_tiempo_visita(
    puntos_visita: List[PuntoVisita],
    origen: str,
    actividades_por_punto: Dict[str, List[int]]
) -> Dict[str, Dict]:
    """
    Distribuye los puntos de visita en días, considerando el tiempo de traslado y actividades.
    Lanza ErrorDeNegocio si la lista de puntos está vacía.
    """
    if not puntos_visita:
        raise ErrorDeNegocio("La lista de puntos de visita está vacía.")
    dias = {}
    dia_actual = 1
    tiempo_dia = 0
    detalle_visitas = []
    prioridad_total_dia = 0
    punto_anterior = origen  # Punto inicial es la sede
    for i, punto in enumerate(puntos_visita):
        traslado_min = get_duracion_minutos(punto_anterior, f"{punto.lat},{punto.long}")
        actividad_min = sum(actividades_por_punto.get(punto.id_pc, [180]))
        tiempo_con_este_punto = tiempo_dia + traslado_min + actividad_min
        retorno_al_origen = get_duracion_minutos(f"{punto.lat},{punto.long}", origen)
        tiempo_con_retorno = tiempo_con_este_punto + retorno_al_origen
        if tiempo_con_retorno > 540:
            dias[f"Día {dia_actual}"] = {
                "detalle": detalle_visitas,
                "retorno_al_origen_min": get_duracion_minutos(punto_anterior, origen),
                "tiempo_total_min": tiempo_dia + get_duracion_minutos(punto_anterior, origen),
                "prioridad_total": prioridad_total_dia
            }
            dia_actual += 1
            detalle_visitas = []
            tiempo_dia = 0
            prioridad_total_dia = 0
            punto_anterior = origen
            traslado_min = get_duracion_minutos(punto_anterior, f"{punto.lat},{punto.long}")
            tiempo_con_este_punto = traslado_min + actividad_min
        detalle_visitas.append({
            "punto": punto,
            "desde": punto_anterior if isinstance(punto_anterior, str) else f"{punto_anterior.lat},{punto_anterior.long}",
            "tiempo_traslado_min": traslado_min,
            "tiempo_actividad_min": actividad_min,
            "prioridad": punto.prioridad if hasattr(punto, 'prioridad') else 0
        })
        tiempo_dia = tiempo_con_este_punto
        prioridad_total_dia += punto.prioridad if hasattr(punto, 'prioridad') else 0
        punto_anterior = punto
    if detalle_visitas:
        dias[f"Día {dia_actual}"] = {
            "detalle": detalle_visitas,
            "retorno_al_origen_min": get_duracion_minutos(f"{punto_anterior.lat},{punto_anterior.long}", origen),
            "tiempo_total_min": tiempo_dia + get_duracion_minutos(f"{punto_anterior.lat},{punto_anterior.long}", origen),
            "prioridad_total": prioridad_total_dia
        }
    return dias

def get_duracion_minutos(origen: str, destino: str) -> float:
    """
    Consulta la API de Google Maps Directions para obtener la duración en minutos entre dos puntos.
    Devuelve 0 si la consulta falla o la respuesta es inválida.
    """
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origen}"
        f"&destination={destino}"
        f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return 0
    data = response.json()
    try:
        return int(data["routes"][0]["legs"][0]["duration"]["value"] / 60)
    except (KeyError, IndexError):
        return 0
