from typing import List
from app.models.schemas import PuntoVisita
from app.db.connection import get_connection
from app.models.models import CentroPoblado, SeleccionPC
from app.services.priorizacion import calcular_priorizacion
from geopy.distance import geodesic
from app.services.exceptions import ErrorDeNegocio
from sqlalchemy import func

#funcion para obtener los puntos de visita desde la base de datos
def obtener_puntos_visita_desde_db() -> List[PuntoVisita]:
    """
    Obtiene la lista de puntos de visita desde la base de datos.
    Lanza ErrorDeNegocio si ocurre un error de conexión o consulta.
    """
    try:
        conn = get_connection()
        if not conn:
            raise ErrorDeNegocio("No se pudo conectar a la base de datos.")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigodece, nombre, CAST(latitud AS float), CAST(longitud AS float),
                   poblacion, cont_avenida, cont_estiaje, cant_lect_metales, sistema_cloro,
                   cant_decla_emerg, pob_menor_12, cant_est_salud, cant_est_edu,
                   conflic_alrededor
            FROM centro_poblado
            WHERE latitud IS NOT NULL AND longitud IS NOT NULL
        """)
        resultados = []

        #recorremos los datos que trajimos de la base de datos y agregamos los puntos de visita a la lista
        for row in cursor.fetchall():
            (codigodece, nombre, latitud, longitud, poblacion, cont_avenida, 
             cont_estiaje, cant_lect_metales, sistema_cloro, cant_decla_emerg,
             pob_menor_12, cant_est_salud, cant_est_edu, conflic_alrededor) = row

            #agregamos los puntos de visita a la lista
            resultados.append(
                PuntoVisita(
                    id_pc=codigodece, 
                    nombre=nombre, 
                    lat=float(latitud), 
                    long=float(longitud),
                    poblacion=poblacion,
                    cont_avenida=cont_avenida,
                    cont_estiaje=cont_estiaje,
                    cant_lect_metales=cant_lect_metales,
                    sistema_cloro=sistema_cloro,
                    cant_decla_emerg=cant_decla_emerg,
                    pob_menor_12=pob_menor_12,
                    cant_est_salud=cant_est_salud,
                    cant_est_edu=cant_est_edu,
                    conflic_alrededor=conflic_alrededor
                )
            )

        cursor.close()
        conn.close()
        return resultados

    except Exception as e:
        raise ErrorDeNegocio(f"Error al procesar puntos de visita: {e}")

def obtener_puntos_seleccionados_priorizados(db, id_analista: int, ultima_fecha) -> List[PuntoVisita]:
    """
    Obtiene y prioriza los puntos seleccionados por un analista en una fecha dada (comparando fecha truncada a segundos).
    """
    puntos_db = db.query(CentroPoblado)\
        .join(SeleccionPC, CentroPoblado.codigodece == SeleccionPC.codigodece)\
        .filter(SeleccionPC.id_analista == id_analista)\
        .filter(func.date_trunc('second', SeleccionPC.fecha_seleccion) == func.date_trunc('second', ultima_fecha))\
        .all()
    
    # Convertir CentroPoblado a PuntoVisita
    puntos_visita = []
    for punto in puntos_db:
        puntos_visita.append(
            PuntoVisita(
                id_pc=punto.codigodece,
                nombre=punto.nombre,
                lat=punto.latitud,
                long=punto.longitud,
                poblacion=punto.poblacion,
                cont_avenida=punto.cont_avenida,
                cont_estiaje=punto.cont_estiaje,
                cant_lect_metales=punto.cant_lect_metales,
                sistema_cloro=punto.sistema_cloro,
                cant_decla_emerg=punto.cant_decla_emerg,
                pob_menor_12=punto.pob_menor_12,
                cant_est_salud=punto.cant_est_salud,
                cant_est_edu=punto.cant_est_edu,
                conflic_alrededor=punto.conflic_alrededor
            )
        )
    
    return calcular_priorizacion(puntos_visita)

def ordenar_puntos_por_origen(puntos: List[PuntoVisita], origen: str) -> List[PuntoVisita]:
    """
    Ordena los puntos de visita por cercanía al origen usando distancia geodésica.
    """
    origen_lat, origen_lng = map(float, origen.split(','))
    return sorted(
        puntos,
        key=lambda p: geodesic((origen_lat, origen_lng), (p.lat, p.long)).km
    )


