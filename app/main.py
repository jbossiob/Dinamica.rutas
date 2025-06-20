from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routers.puntos_visita import router as puntos_visita_router
from app.routers.seleccion import router as seleccion_router
from app.routers.ruta_optima import router as ruta_optima_router
from app.routers.actividad import router as actividad_router
from app.routers.historial_rutas import router as historial_rutas_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_cors_origins

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Planificacion ODS -Ruta Optima",
    version="1.0.0",
    description="API para planificación de rutas óptimas para ODS",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuración de CORS mejorada
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
    ],
    expose_headers=["Content-Length", "Content-Range"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

app.include_router(puntos_visita_router)
app.include_router(seleccion_router)
app.include_router(ruta_optima_router)
app.include_router(actividad_router)
app.include_router(historial_rutas_router)

@app.get("/")
def root():
    return {"mensaje": "API Planificacion ODS - Ruta Optima funcionando"}