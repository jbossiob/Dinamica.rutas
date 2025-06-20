import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Configuración según entorno
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Configuración para producción
        host = os.getenv("HOST", "0.0.0.0")  # Acepta conexiones externas
        port = int(os.getenv("PORT", "8000"))
        reload = False
        log_level = "info"
    else:
        # Configuración para desarrollo
        host = os.getenv("HOST", "127.0.0.1")  # Solo conexiones locales
        port = int(os.getenv("PORT", "8000"))
        reload = True
        log_level = "debug"
    
    print(f"🚀 Iniciando servidor en modo: {environment}")
    print(f"📍 Host: {host}")
    print(f"🔌 Puerto: {port}")
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=reload,
        workers=1,
        log_level=log_level
    )