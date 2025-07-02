from fastapi import FastAPI
from dotenv import load_dotenv
import os
import logging
from app.routers.mapa import router as mapa_router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_cors_origins
from fastapi.staticfiles import StaticFiles

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Cargar variables de entorno
load_dotenv()

app = FastAPI(
    title="Mapa de generacion de rutas - juego",
    version="1.0.0",
    description="Juego interactivo para generar rutas optimas",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Montar archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

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

print("CORS Origins habilitados:", get_cors_origins())

app.include_router(mapa_router)

@app.get("/")
def root():
    return {"mensaje": "API Planificacion ODS - Ruta Optima funcionando"}