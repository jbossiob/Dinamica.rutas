import math
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    R = 6371  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def validar_lista_no_vacia(lista, nombre="lista"):
    """
    Lanza una excepción si la lista es None, no es lista o está vacía.
    """
    if not lista or not isinstance(lista, list):
        raise ValueError(f"{nombre} es inválida o está vacía.")

def validar_dict_no_vacio(dic, nombre="diccionario"):
    """
    Lanza una excepción si el diccionario es None, no es dict o está vacío.
    """
    if not dic or not isinstance(dic, dict):
        raise ValueError(f"{nombre} es inválido o está vacío.")

def validar_entero_positivo(valor, nombre="valor"):
    """
    Lanza una excepción si el valor no es un entero positivo.
    """
    if not isinstance(valor, int) or valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")

def formatear_fecha_iso(fecha: datetime) -> str:
    """
    Devuelve la fecha en formato ISO 8601, o una cadena vacía si es None.
    """
    return fecha.isoformat() if fecha else ""