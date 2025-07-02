import requests
import numpy as np
import folium
import googlemaps
from sklearn.cluster import DBSCAN
from math import radians, cos, sin, asin, sqrt
import os
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from app.services.exceptions import ServicioExternoError
import polyline  # <--- Aseguramos la importación

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
SHEETDB_URL = os.getenv("API_SHEET_URL")
HOTEL_MELIA_LIMA_COORDS = tuple(map(float, os.getenv("HOTEL_MELIA_LIMA_COORDS").split(',')))  # Latitud, Longitud
HOTEL_MELIA_LIMA_DIRECCION = os.getenv("HOTEL_MELIA_LIMA_DIRECCION")  # Dirección textual opcional
DISTANCIA_AGRUPAMIENTO_KM = 0.5
EARTH_RADIUS_KM = 6371.0

class PuntoVisita:
    """Clase para representar un punto de visita"""
    def __init__(self, lat: float, lon: float, direccion: str, fecha: str):
        self.lat = lat
        self.lon = lon
        self.direccion = direccion
        self.fecha = fecha

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos usando la fórmula de Haversine
    """
    # Convertir a radianes
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Diferencia de coordenadas
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Fórmula de Haversine
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return EARTH_RADIUS_KM * c

def obtener_datos_google_sheets() -> List[Dict]:
    """
    Obtiene datos desde la API de Google Sheets
    """
    try:
        logger.info("Obteniendo datos desde Google Sheets...")
        response = requests.get(SHEETDB_URL, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Datos obtenidos exitosamente: {len(data)} registros")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener datos de Google Sheets: {e}")
        raise ServicioExternoError(f"Error al obtener datos de Google Sheets: {e}")
    except Exception as e:
        logger.error(f"Error inesperado al obtener datos: {e}")
        raise ServicioExternoError(f"Error inesperado al obtener datos: {e}")

def validar_y_convertir_puntos(datos: List[Dict]) -> List[PuntoVisita]:
    """
    Valida y convierte los registros en objetos PuntoVisita
    """
    puntos_validos = []
    
    for registro in datos:
        try:
            # Validar que existan los campos requeridos
            if not all(campo in registro for campo in ['Latitud', 'Longitud', 'Dirección', 'FechaHora']):
                logger.warning(f"Registro incompleto, saltando: {registro}")
                continue
            
            # Convertir coordenadas a float
            lat = float(registro['Latitud'])
            lon = float(registro['Longitud'])
            
            # Validar rango de coordenadas
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning(f"Coordenadas fuera de rango válido: lat={lat}, lon={lon}")
                continue
            
            # Crear punto válido
            punto = PuntoVisita(
                lat=lat,
                lon=lon,
                direccion=registro['Dirección'],
                fecha=registro['FechaHora']
            )
            puntos_validos.append(punto)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error al convertir registro: {registro}, error: {e}")
            continue
    
    logger.info(f"Puntos válidos convertidos: {len(puntos_validos)} de {len(datos)}")
    return puntos_validos

def agrupar_puntos_geograficamente(puntos: List[PuntoVisita]) -> List[List[PuntoVisita]]:
    """
    Agrupa puntos geográficamente cercanos usando DBSCAN
    """
    if not puntos:
        return []
    
    # Preparar datos para DBSCAN
    coords = np.array([[p.lat, p.lon] for p in puntos])
    
    # Convertir distancia de km a grados (aproximadamente)
    # 1 grado ≈ 111 km en el ecuador
    eps_grados = DISTANCIA_AGRUPAMIENTO_KM / 111.0
    
    # Aplicar DBSCAN
    clustering = DBSCAN(eps=eps_grados, min_samples=1).fit(coords)
    
    # Agrupar puntos por cluster
    grupos = {}
    for i, label in enumerate(clustering.labels_):
        if label not in grupos:
            grupos[label] = []
        grupos[label].append(puntos[i])
    
    grupos_lista = list(grupos.values())
    logger.info(f"Puntos agrupados en {len(grupos_lista)} grupos")
    
    return grupos_lista

def geocode_address(address, gmaps_client):
    geocode_result = gmaps_client.geocode(address)
    if geocode_result and 'geometry' in geocode_result[0]:
        location = geocode_result[0]['geometry']['location']
        return (location['lat'], location['lng'])
    return None

def obtener_ruta_optimizada_grupo(gmaps_client, grupo: List[PuntoVisita]) -> Optional[Dict]:
    """
    Obtiene la ruta optimizada para un grupo de puntos usando Google Maps,
    siempre partiendo del origen fijo (HOTEL MELIA LIMA) y pasando por los puntos agrupados.
    El origen puede ser una dirección textual si está definida en la variable de entorno HOTEL_MELIA_LIMA_DIRECCION.
    """
    try:
        if len(grupo) == 0:
            logger.info("Grupo vacío, no se genera ruta.")
            return None

        # Origen: dirección textual si está definida, si no, coordenadas
        if HOTEL_MELIA_LIMA_DIRECCION:
            origen = HOTEL_MELIA_LIMA_DIRECCION
        else:
            origen = f"{HOTEL_MELIA_LIMA_COORDS[0]},{HOTEL_MELIA_LIMA_COORDS[1]}"
        # Destino: último punto del grupo
        destino = f"{grupo[-1].lat},{grupo[-1].lon}"
        # Waypoints: todos los puntos menos el último (si hay más de uno)
        waypoints = [f"{p.lat},{p.lon}" for p in grupo[:-1]] if len(grupo) > 1 else None

        directions_result = gmaps_client.directions(
            origin=origen,
            destination=destino,
            waypoints=waypoints,
            optimize_waypoints=True if waypoints else False,
            mode="driving"
        )

        logger.info(f"Respuesta Google Maps grupo ({len(grupo)} puntos): {directions_result}")

        if not directions_result:
            logger.warning(f"No se pudo obtener ruta para grupo con {len(grupo)} puntos")
            return None
        else:
            logger.info(f"Ruta obtenida para grupo con {len(grupo)} puntos: {directions_result[0]}")

        # Reordenar los puntos según el orden optimizado (si hay waypoints)
        ruta = directions_result[0]
        if 'waypoint_order' in ruta and len(grupo) > 1:
            orden = ruta['waypoint_order']
            grupo_ordenado = [grupo[:-1][i] for i in orden] + [grupo[-1]]
        else:
            grupo_ordenado = grupo

        return {'ruta': ruta, 'grupo_ordenado': grupo_ordenado}

    except Exception as e:
        logger.error(f"Error al obtener ruta optimizada para grupo: {e}")
        return None

def crear_mapa_interactivo(grupos_rutas: List[Tuple[List[PuntoVisita], Optional[Dict]]]) -> str:
    """
    Crea un mapa interactivo con todas las rutas
    """
    # Inicializar cliente Google Maps
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    gmaps_client = googlemaps.Client(key=api_key)

    # Determinar coordenadas del origen
    if HOTEL_MELIA_LIMA_DIRECCION:
        origen_coords = geocode_address(HOTEL_MELIA_LIMA_DIRECCION, gmaps_client)
        if not origen_coords:
            origen_coords = HOTEL_MELIA_LIMA_COORDS
    else:
        origen_coords = HOTEL_MELIA_LIMA_COORDS

    # Crear mapa centrado en el origen real
    mapa = folium.Map(
        location=origen_coords,
        zoom_start=17,
        tiles='OpenStreetMap'
    )
    
    # Colores para diferenciar rutas
    colores = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
               'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 
               'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 
               'lightgray']
    
    # Agregar punto de salida (HOTEL MELIA LIMA) destacado
    folium.Marker(
        origen_coords,
        popup='<b style="color:#0a1172;font-size:16px;">★ ORIGEN: HOTEL MELIA LIMA</b><br><span style="color:#0a1172;">Av. Salaverry 2599, San Isidro, Lima, Perú</span>',
        icon=folium.Icon(color='darkblue', icon='star')
    ).add_to(mapa)
    
    # Procesar cada grupo
    for i, (grupo, ruta_data) in enumerate(grupos_rutas):
        color = colores[i % len(colores)]
        # Usar grupo_ordenado si está disponible
        if ruta_data and isinstance(ruta_data, dict) and 'grupo_ordenado' in ruta_data:
            grupo = ruta_data['grupo_ordenado']
            ruta = ruta_data['ruta']
        else:
            ruta = ruta_data
        
        # Agregar puntos del grupo
        for punto in grupo:
            folium.Marker(
                [punto.lat, punto.lon],
                popup=f'<b>Punto de visita</b><br>Dirección: {punto.direccion}<br>Fecha: {punto.fecha}',
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(mapa)
        
        # Log de depuración para ver la respuesta de Google Maps
        if ruta:
            logger.info(f"Ruta para grupo {i+1}: {ruta}")
            if 'overview_polyline' not in ruta:
                logger.warning(f"NO HAY overview_polyline para grupo {i+1}. Claves disponibles: {list(ruta.keys())}")
        # Agregar ruta si existe
        if ruta and 'overview_polyline' in ruta:
            try:
                polyline_points = polyline.decode(ruta['overview_polyline']['points'])
                folium.PolyLine(
                    locations=polyline_points,
                    weight=3,
                    color=color,
                    opacity=0.8,
                    popup=f'Ruta Grupo {i+1}'
                ).add_to(mapa)
            except Exception as e:
                logger.error(f"Error al dibujar ruta para grupo {i+1}: {e}")
    
    # Guardar mapa
    archivo_html = "rutas_hotel_melia_lima.html"
    mapa.save(archivo_html)
    logger.info(f"Mapa guardado como {archivo_html}")
    
    return archivo_html

def generar_mapa_rutas() -> str:
    """
    Función principal que ejecuta todo el proceso de generación de rutas
    """
    try:
        # 1. Obtener datos de Google Sheets
        datos = obtener_datos_google_sheets()
        
        # 2. Convertir a puntos válidos
        puntos = validar_y_convertir_puntos(datos)
        
        if not puntos:
            raise ServicioExternoError("No se encontraron puntos válidos en los datos")
        
        # 3. Agrupar puntos geográficamente
        grupos = agrupar_puntos_geograficamente(puntos)
        
        # 4. Inicializar cliente de Google Maps
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ServicioExternoError("GOOGLE_MAPS_API_KEY no está configurada")
        
        gmaps_client = googlemaps.Client(key=api_key)
        
        # 5. Obtener rutas optimizadas para cada grupo
        grupos_rutas = []
        for grupo in grupos:
            ruta_data = obtener_ruta_optimizada_grupo(gmaps_client, grupo)
            grupos_rutas.append((grupo, ruta_data))
        
        # 6. Crear mapa interactivo
        archivo_html = crear_mapa_interactivo(grupos_rutas)
        
        logger.info("Proceso de generación de rutas completado exitosamente")
        return archivo_html
        
    except Exception as e:
        logger.error(f"Error en el proceso de generación de rutas: {e}")
        raise ServicioExternoError(f"Error en el proceso de generación de rutas: {e}")

def leer_archivo_html(archivo_html: str) -> str:
    """
    Lee el contenido del archivo HTML generado
    """
    try:
        with open(archivo_html, 'r', encoding='utf-8') as f:
            contenido = f.read()
        return contenido
    except FileNotFoundError:
        raise ServicioExternoError(f"Archivo {archivo_html} no encontrado")
    except Exception as e:
        raise ServicioExternoError(f"Error al leer archivo HTML: {e}") 