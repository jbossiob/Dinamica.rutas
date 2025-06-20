import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    # Configuración para producción
    host = os.getenv("HOST", "0.0.0.0")  # 0.0.0.0 para producción
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=False,  # Deshabilitar reload en producción
        workers=1,     # Ajustar según necesidades
        log_level="info"
    )