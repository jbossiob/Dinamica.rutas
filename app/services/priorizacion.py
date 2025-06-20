from typing import List
from app.models.schemas import PuntoVisita
from app.services.exceptions import ErrorDeNegocio

def calcular_priorizacion(puntos_visita: List[PuntoVisita]) -> List[PuntoVisita]:
    """
    Calcula y asigna la prioridad a cada punto de visita según sus criterios y si es característico.
    Lanza ErrorDeNegocio si la lista está vacía o los datos son inválidos.
    """
    if not puntos_visita or not isinstance(puntos_visita, list):
        raise ErrorDeNegocio("La lista de puntos de visita es inválida o está vacía.")
    try:
        # Filtrar valores None y usar 0 como valor por defecto
        max_poblacion = max(p.poblacion for p in puntos_visita) or 1
        max_cont_avenida = max(p.cont_avenida or 0 for p in puntos_visita) or 1
        max_cont_estiaje = max(p.cont_estiaje or 0 for p in puntos_visita) or 1
        max_cant_lect_metales = max(p.cant_lect_metales or 0 for p in puntos_visita) or 1
        max_sistema_cloro = max(1 if p.sistema_cloro else 0 for p in puntos_visita) or 1
        max_cant_decla_emerg = max(p.cant_decla_emerg or 0 for p in puntos_visita) or 1
        max_pob_menor_12 = max(p.pob_menor_12 or 0 for p in puntos_visita) or 1
        max_cant_est_salud = max(p.cant_est_salud or 0 for p in puntos_visita) or 1
        max_cant_est_edu = max(p.cant_est_edu or 0 for p in puntos_visita) or 1
        max_conflic_alrededor = max(p.conflic_alrededor or 0 for p in puntos_visita) or 1

    except Exception:
        raise ErrorDeNegocio("No se pudo calcular la priorización por datos faltantes o inválidos.")
    
    for p in puntos_visita:
        poblacion_norm = p.poblacion / max_poblacion
        cont_avenida_norm = (p.cont_avenida or 0) / max_cont_avenida
        cont_estiaje_norm = (p.cont_estiaje or 0) / max_cont_estiaje
        cant_lect_metales_norm = (p.cant_lect_metales or 0) / max_cant_lect_metales
        sistema_cloro_norm = (1 if p.sistema_cloro else 0) / max_sistema_cloro
        cant_decla_emerg_norm = (p.cant_decla_emerg or 0) / max_cant_decla_emerg
        pob_menor_12_norm = (p.pob_menor_12 or 0) / max_pob_menor_12
        cant_est_salud_norm = (p.cant_est_salud or 0) / max_cant_est_salud
        cant_est_edu_norm = (p.cant_est_edu or 0) / max_cant_est_edu
        conflic_alrededor_norm = (p.conflic_alrededor or 0) / max_conflic_alrededor

        #prioridades segun la matriz de prioridades
        p.prioridad = (
            0.17 * cont_avenida_norm +
            0.17 * cont_estiaje_norm +
            0.09 * cant_lect_metales_norm +
            0.09 * sistema_cloro_norm +
            0.09 * cant_decla_emerg_norm +
            0.2 * pob_menor_12_norm +
            0.03 * cant_est_salud_norm +
            0.03 * cant_est_edu_norm +
            0.13 * conflic_alrededor_norm
        )
    puntos_visita_ordenados = sorted(puntos_visita, key=lambda x: x.prioridad, reverse=True)
    return puntos_visita_ordenados








