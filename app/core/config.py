from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Configuración para el servicio de mapas
MAP_CONFIG = {
    "sheetdb_url": os.getenv("API_SHEET_URL"),
    "hotel_melia_lima_coords": (-12.0926987, -77.0552319),
    "distancia_agrupamiento_km": 0.5,
    "earth_radius_km": 6371.0
}

# Configuración de CORS desde variables de entorno
def get_cors_origins():
    """Retorna los orígenes permitidos desde variables de entorno"""
    cors_origins_env = os.getenv("CORS_ORIGINS")
    
    if not cors_origins_env:
        raise ValueError(
            "La variable de entorno CORS_ORIGINS debe estar configurada. "
            "Ejemplo: CORS_ORIGINS=https://make.powerapps.com,https://apps.powerapps.com"
        )
    
    origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    
    if not origins:
        raise ValueError(
            "CORS_ORIGINS no puede estar vacío. "
            "Debe contener al menos un origen válido."
        )
    
    # Validar que los orígenes sean URLs válidas
    for origin in origins:
        if not (origin.startswith("http://") or origin.startswith("https://")):
            raise ValueError(
                f"Origen inválido en CORS_ORIGINS: {origin}. "
                "Los orígenes deben comenzar con http:// o https://"
            )
    
    return origins

