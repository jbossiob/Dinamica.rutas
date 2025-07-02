from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse
import logging
from app.services.mapa_rutas import generar_mapa_rutas, leer_archivo_html
from app.services.exceptions import ServicioExternoError

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mapa", tags=["Mapa de Rutas"])

@router.get("/rutas", response_class=HTMLResponse)
async def obtener_mapa_rutas():
    """
    Endpoint para generar y obtener el mapa de rutas optimizadas
    
    Este endpoint:
    1. Obtiene datos desde Google Sheets
    2. Convierte los registros en puntos de visita
    3. Agrupa puntos geográficamente cercanos
    4. Calcula rutas optimizadas usando Google Maps
    5. Genera un mapa interactivo con todas las rutas
    6. Retorna el archivo HTML del mapa
    
    Returns:
        HTMLResponse: Contenido HTML del mapa interactivo
        
    Raises:
        HTTPException: Si hay errores en el proceso de generación
    """
    try:
        logger.info("Iniciando generación de mapa de rutas...")
        
        # Generar el mapa de rutas
        archivo_html = generar_mapa_rutas()
        
        # Leer el contenido del archivo HTML
        contenido_html = leer_archivo_html(archivo_html)
        
        logger.info("Mapa de rutas generado y entregado exitosamente")
        
        # Retornar el contenido HTML
        return HTMLResponse(
            content=contenido_html,
            status_code=200,
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except ServicioExternoError as e:
        logger.error(f"Error de servicio externo: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Error en servicio externo: {str(e)}"
        )
        
    except Exception as e:
        logger.error(f"Error inesperado al generar mapa de rutas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/status")
async def estado_mapa_rutas():
    """
    Endpoint para verificar el estado del servicio de mapas
    
    Returns:
        dict: Estado del servicio y configuración
    """
    try:
        import os
        import requests
        
        # Verificar configuración
        config_status = {
            "google_maps_api_key": "configurada" if os.getenv('GOOGLE_MAPS_API_KEY') else "no configurada",
            "sheetdb_url": os.getenv("API_SHEET_URL"),
            "hotel_melia_lima_coords": "(-12.0926987, -77.0552319)",
            "distancia_agrupamiento_km": 0.5
        }
        
        # Verificar conectividad con SheetDB
        try:
            response = requests.get(os.getenv("API_SHEET_URL"), timeout=10)
            sheetdb_status = "conectado" if response.status_code == 200 else f"error {response.status_code}"
        except Exception as e:
            sheetdb_status = f"error de conexión: {str(e)}"
        
        return {
            "status": "operativo",
            "configuracion": config_status,
            "sheetdb_status": sheetdb_status,
            "mensaje": "Servicio de mapas disponible"
        }
        
    except Exception as e:
        logger.error(f"Error al verificar estado: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al verificar estado: {str(e)}"
        ) 