from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import SeleccionPC, SeleccionActividad, Actividad
from sqlalchemy import func
from app.services.puntos_visita import obtener_puntos_seleccionados_priorizados
from app.services.tiempo_visita import distribuir_tiempo_visita, obtener_tiempo_por_punto
from app.services.ruta_optima import (
    construir_url_google_maps, consultar_ruta_google_maps, insertar_ruta_generada, insertar_historial_ruta,
    construir_waypoints, procesar_datos_ruta, construir_url_gmaps, armar_respuesta_detallada
)
import logging
from app.services.exceptions import ServicioExternoError, ErrorDeNegocio
import os

router = APIRouter()
logger = logging.getLogger("ruta_optima")

@router.get("/ruta-optima")
def calcular_ruta_optima(id_analista: int, db: Session = Depends(get_db)):
 
    try:
        ultima_fecha = (
            db.query(func.date_trunc('second', SeleccionPC.fecha_seleccion))
            .filter(SeleccionPC.id_analista == id_analista)
            .order_by(func.date_trunc('second', SeleccionPC.fecha_seleccion).desc())
            .limit(1)
            .scalar()
        )

        if not ultima_fecha:
            raise HTTPException(status_code=400, detail="No hay seleccion activa")

        # Obtener la seleccion activa del analista y priorizar
        puntos = obtener_puntos_seleccionados_priorizados(db, id_analista, ultima_fecha)
        origen = os.getenv("ORIGEN_COORDS", "-5.189773,-80.6406592")
        destino = origen
        logger.info("Puntos de visita seleccionados:")
        for p in puntos:
            logger.info(f"{p.nombre}, {p.lat}, {p.long}")
        seleccion_actividades = (
            db.query(SeleccionActividad)
            .join(Actividad)
            .filter(SeleccionActividad.id_analista == id_analista)
            .all()
        )

        # Mapear: codigodece => Lista de actividades
        actividades_por_punto = obtener_tiempo_por_punto(db, id_analista)

        #distribuir el tiempo de visita a los puntos de visita
        distribucion_dias = distribuir_tiempo_visita(puntos, origen, actividades_por_punto)

        # Reordenar días por prioridad de ruta
        distribucion_dias_ordenada = dict(
            sorted(
                distribucion_dias.items(),
                key=lambda item: item[1]["prioridad_total"],
                reverse=True
            )
        )

        # Re-etiquetar como Día 1, Día 2, etc.
        distribucion_final = {
            f"Día {i+1}": {
                "puntos": [p["punto"] for p in dia["detalle"]],
                "tiempo_total_min": dia["tiempo_total_min"],
                "prioridad_total": dia["prioridad_total"]
            }
            for i, (_, dia) in enumerate(distribucion_dias_ordenada.items())
        }

        #Construir waypoints (todos los puntos seleccionados)
        waypoints = construir_waypoints(puntos)

        #armamos URL para la API de Google Maps
        url = construir_url_google_maps(origen, destino, waypoints)
        logger.info(f"URL enviada a Google: {url}")

        #Hacemos la peticion a la API de Google Maps
        data = consultar_ruta_google_maps(url)

        if not data["routes"]:
            logger.error(f"Respuesta completa de Google: {data}")
            raise HTTPException(status_code=400, detail="No se pudo calcular la ruta óptima")

        puntos_ordenados, ruta_optima, distancia_total_km, duracion_total_min = procesar_datos_ruta(data, puntos)
        url_gmaps = construir_url_gmaps(origen, destino, puntos_ordenados)

        # 1. Calcular prioridad total de la ruta
        prioridad_total = sum(p.prioridad for p in puntos_ordenados)

        # 2. Insertar en rutas_generadas (tabla de historial de rutas de la BD)
        ruta_generada = insertar_ruta_generada(db, id_analista, duracion_total_min, distancia_total_km, prioridad_total)

        # 3. Insertar puntos en historial_ruta
        insertar_historial_ruta(db, ruta_generada.id, distribucion_final)

        return armar_respuesta_detallada(
            origen, destino, ruta_optima, puntos_ordenados, distancia_total_km, duracion_total_min, url_gmaps, distribucion_final, db, id_analista
        )
    except ServicioExternoError as e:
        logger.error(str(e))
        raise HTTPException(status_code=502, detail=str(e))
    except ErrorDeNegocio as e:
        logger.error(str(e))
        raise HTTPException(status_code=400, detail=str(e))
