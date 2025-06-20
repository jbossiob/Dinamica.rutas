import os
import requests
from app.models.models import RutasGeneradas, HistorialRuta, SeleccionActividad, Actividad
from datetime import datetime
from polyline import decode as decode_polyline
from app.services.exceptions import ServicioExternoError
from app.services.utils import haversine
from app.services.tiempo_visita import obtener_tiempo_por_punto
from sqlalchemy.orm import Session

# Constantes configurables
ORIGEN_NOMBRE = os.getenv("ORIGEN_NOMBRE", "SUNASS ODS Piura")
OBSERVACION_RUTA = os.getenv("OBSERVACION_RUTA", "Ruta generada automáticamente")

# Utilidad para validar respuestas de APIs externas

def validar_respuesta_api(data, clave_principal="routes"):
    if clave_principal not in data or not data[clave_principal]:
        raise ServicioExternoError(f"Respuesta inválida de API externa: no se encontró '{clave_principal}' o está vacío.")
    return True

# Construye la URL para la API de Google Maps Directions

def construir_url_google_maps(origen: str, destino: str, waypoints: str) -> str:
    return (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origen}"
        f"&destination={destino}"
        f"&waypoints=optimize:false|{waypoints}"
        f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
    )

# Realiza la petición a la API de Google Maps Directions y retorna la respuesta en formato JSON

def consultar_ruta_google_maps(url: str) -> dict:
    response = requests.get(url)
    if response.status_code != 200:
        raise ServicioExternoError("Error al consultar Google Maps API")
    data = response.json()
    validar_respuesta_api(data, "routes")
    return data

# Inserta una nueva ruta generada en la base de datos y la retorna

def insertar_ruta_generada(db, id_analista, duracion_total_min, distancia_total_km, prioridad_total, observaciones=None):
    ruta_generada = RutasGeneradas(
        id_analista=id_analista,
        fecha_generacion=datetime.now(),
        duracion_total_min=duracion_total_min,
        distancia_total_km=distancia_total_km,
        prioridad_total=prioridad_total,
        observaciones=observaciones or OBSERVACION_RUTA
    )
    db.add(ruta_generada)
    db.commit()
    db.refresh(ruta_generada)
    return ruta_generada

# Inserta el historial de puntos de visita para una ruta generada

def insertar_historial_ruta(db, ruta_id, distribucion_final):
    for i, (nombre_dia, datos_dia) in enumerate(distribucion_final.items(), start=1):
        punto_anterior = None
        for orden, punto in enumerate(datos_dia["puntos"]):
            if orden == 0:
                distancia_km = 0
            else:
                distancia_km = haversine(
                    punto_anterior.lat, punto_anterior.long,
                    punto.lat, punto.long
                )
            historial = HistorialRuta(
                id_ruta=ruta_id,
                codigodece=punto.id_pc,
                orden_visita=orden + 1,
                dia_ruta=i,
                prioridad=punto.prioridad if hasattr(punto, 'prioridad') else 0,
                tiempo_estimado_min=datos_dia["tiempo_total_min"],
                distancia_km=distancia_km
            )
            db.add(historial)
            punto_anterior = punto
    db.commit()

# Construye el string de waypoints para la API de Google Maps

def construir_waypoints(puntos):
    return "|".join([
        f"{p.lat},{p.long}"
        for p in puntos
        if p.lat is not None and p.long is not None
    ])

# Procesa la respuesta de la API de Google Maps para extraer la polyline, distancia y duración total

def procesar_datos_ruta(data, puntos):
    polyline = data["routes"][0]["overview_polyline"]["points"]
    ruta_optima = decode_polyline(polyline)
    distancia_total_km = sum(leg["distance"]["value"] for leg in data["routes"][0]["legs"]) / 1000
    duracion_total_min = sum(leg["duration"]["value"] for leg in data["routes"][0]["legs"]) / 60
    # Por ahora, se retorna la lista de puntos en el mismo orden recibido
    puntos_ordenados = puntos
    return puntos_ordenados, ruta_optima, distancia_total_km, duracion_total_min

# Construye el link para abrir la ruta en Google Maps en modo dirección

def construir_url_gmaps(origen, destino, puntos_ordenados):
    waypoints_ordenados = construir_waypoints(puntos_ordenados)
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={origen}"
        f"&destination={destino}"
        f"&travelmode=driving"
        f"&waypoints={waypoints_ordenados}"
    )

# Construye la URL de Google Maps Directions para los puntos de un día específico

def construir_url_gmaps_dia(origen: str, destino: str, puntos_dia) -> str:
    """
    Construye la URL de Google Maps Directions para los puntos de un día específico.
    """
    waypoints = "|".join([f"{p.lat},{p.long}" for p in puntos_dia])
    return (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={origen}"
        f"&destination={destino}"
        f"&travelmode=driving"
        f"&waypoints={waypoints}"
    )

def obtener_polyline_dia(origen: str, destino: str, puntos_dia) -> list:
    """
    Consulta la API de Google Maps Directions para obtener la polyline (array de coordenadas) de la ruta de un día.
    """
    waypoints = "|".join([f"{p.lat},{p.long}" for p in puntos_dia])
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origen}"
        f"&destination={destino}"
        f"&waypoints=optimize:false|{waypoints}"
        f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    try:
        polyline = data["routes"][0]["overview_polyline"]["points"]
        return decode_polyline(polyline)
    except (KeyError, IndexError):
        return []

# Arma la respuesta final del endpoint de ruta óptima

def armar_respuesta_final(origen, destino, ruta_optima, puntos_ordenados, distancia_total_km, duracion_total_min, url_gmaps, distribucion_final):
    # Obtener actividades por punto para incluir en la respuesta
    from app.services.tiempo_visita import obtener_tiempo_por_punto
    
    # Necesitamos acceder a la base de datos para obtener las actividades
    # Por ahora, vamos a crear una función auxiliar que reciba la db como parámetro
    return {
        "origen": ORIGEN_NOMBRE,
        "destino": destino,
        "ruta_optima": ruta_optima,
        "puntos_ordenados": puntos_ordenados,
        "distancia_total_km": round(distancia_total_km, 2),
        "duracion_total_min": round(duracion_total_min, 2),
        "url_gmaps": url_gmaps,
        "distribucion_dias": distribucion_final
    }

def armar_respuesta_detallada(origen, destino, ruta_optima, puntos_ordenados, distancia_total_km, duracion_total_min, url_gmaps, distribucion_final, db: Session, id_analista: int):
    """
    Arma la respuesta final con información detallada de cada día incluyendo flujo de ruta, distancias, tiempos y actividades.
    """
    # Obtener actividades por punto
    actividades_por_punto = {}
    seleccion_actividades = (
        db.query(SeleccionActividad.codigodece, Actividad.nombre, Actividad.duracion_min)
        .join(Actividad, SeleccionActividad.id_actividad == Actividad.id)
        .filter(SeleccionActividad.id_analista == id_analista)
        .all()
    )
    
    for codigodece, nombre_actividad, duracion in seleccion_actividades:
        if codigodece not in actividades_por_punto:
            actividades_por_punto[codigodece] = []
        actividades_por_punto[codigodece].append({
            "actividad": nombre_actividad,
            "tiempo": duracion
        })
    
    # Construir respuesta detallada por día
    dias_detallados = []
    
    for i, (nombre_dia, datos_dia) in enumerate(distribucion_final.items(), start=1):
        puntos_dia = datos_dia["puntos"]
        tiempo_total_dia = datos_dia["tiempo_total_min"]
        
        # Obtener polyline y URL para este día
        url_gmaps_dia = construir_url_gmaps_dia(origen, destino, puntos_dia)
        ruta_optima_dia = obtener_polyline_dia(origen, destino, puntos_dia)
        
        # Construir flujo de ruta para este día
        flujo_ruta = []
        punto_anterior = origen
        
        # Punto de partida
        flujo_ruta.append({
            "punto_partida": {
                "nombre": ORIGEN_NOMBRE,
                "coordenadas": origen
            }
        })
        
        # Procesar cada punto de control del día
        for j, punto in enumerate(puntos_dia):
            # Calcular distancia y tiempo desde el punto anterior
            if j == 0:
                # Para el primer punto, calcular desde el origen
                distancia_desde_anterior, tiempo_desde_anterior = obtener_distancia_y_tiempo_viaje(
                    origen,
                    f"{punto.lat},{punto.long}"
                )
            else:
                # Para los demás puntos, calcular desde el punto anterior
                distancia_desde_anterior, tiempo_desde_anterior = obtener_distancia_y_tiempo_viaje(
                    f"{puntos_dia[j-1].lat},{puntos_dia[j-1].long}",
                    f"{punto.lat},{punto.long}"
                )
            
            # Obtener actividades para este punto
            actividades_punto = actividades_por_punto.get(str(punto.id_pc), [])
            
            punto_detalle = {
                f"pc_{j+1}": {
                    "nombre": punto.nombre,
                    "codigodece": punto.id_pc,
                    "coordenadas": f"{punto.lat},{punto.long}",
                    "distancia_desde_anterior": round(distancia_desde_anterior, 2),
                    "tiempo_desde_anterior": tiempo_desde_anterior,
                    "actividad_a_realizarse": {
                        "actividades": actividades_punto,
                        "tiempo_total_actividades": sum(act["tiempo"] for act in actividades_punto)
                    }
                }
            }
            flujo_ruta.append(punto_detalle)
        
        # Agregar retorno al origen
        if puntos_dia:
            ultimo_punto = puntos_dia[-1]
            distancia_retorno, tiempo_retorno = obtener_distancia_y_tiempo_viaje(
                f"{ultimo_punto.lat},{ultimo_punto.long}",
                origen
            )
            
            flujo_ruta.append({
                "retorno": {
                    "destino": ORIGEN_NOMBRE,
                    "coordenadas": origen,
                    "distancia_desde_anterior": round(distancia_retorno, 2),
                    "tiempo_desde_anterior": tiempo_retorno
                }
            })
        
        dia_detallado = {
            "dia": nombre_dia,
            "ruta": ruta_optima_dia,
            "pc_a_visitar": len(puntos_dia),
            "tiempo_total_dia": round(tiempo_total_dia, 2),
            "flujo_de_la_ruta": flujo_ruta,
            "url_gmaps_dia": url_gmaps_dia
        }
        
        dias_detallados.append(dia_detallado)
    
    return {
        "origen": ORIGEN_NOMBRE,
        "destino": destino,
        "ruta_optima": ruta_optima,
        "distancia_total_km": round(distancia_total_km, 2),
        "duracion_total_min": round(duracion_total_min, 2),
        "url_gmaps": url_gmaps,
        "dias": dias_detallados
    }

def obtener_distancia_y_tiempo_viaje(origen: str, destino: str) -> tuple:
    """
    Obtiene la distancia y tiempo de viaje entre dos puntos usando Google Maps API.
    Retorna (distancia_km, tiempo_minutos)
    """
    url = (
        f"https://maps.googleapis.com/maps/api/directions/json"
        f"?origin={origen}"
        f"&destination={destino}"
        f"&key={os.getenv('GOOGLE_MAPS_API_KEY')}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return (0, 0)
    data = response.json()
    try:
        distancia_km = data["routes"][0]["legs"][0]["distance"]["value"] / 1000
        tiempo_minutos = int(data["routes"][0]["legs"][0]["duration"]["value"] / 60)
        return (distancia_km, tiempo_minutos)
    except (KeyError, IndexError):
        return (0, 0)

def obtener_tiempo_viaje(origen: str, destino: str) -> int:
    """
    Obtiene el tiempo de viaje entre dos puntos usando Google Maps API.
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