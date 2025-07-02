#!/usr/bin/env python3
"""
Script de prueba para la funcionalidad de mapa de rutas
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_URL = "http://localhost:8000"
MAP_ENDPOINT = f"{BASE_URL}/mapa/rutas"
STATUS_ENDPOINT = f"{BASE_URL}/mapa/status"

def test_status_endpoint():
    """Prueba el endpoint de estado"""
    print("🔍 Probando endpoint de estado...")
    
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Estado del servicio:")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Google Maps API: {data.get('configuracion', {}).get('google_maps_api_key')}")
            print(f"   - SheetDB: {data.get('sheetdb_status')}")
            print(f"   - Mensaje: {data.get('mensaje')}")
            return True
        else:
            print(f"❌ Error en status endpoint: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def test_mapa_rutas_endpoint():
    """Prueba el endpoint de generación de mapa"""
    print("\n🗺️  Probando generación de mapa de rutas...")
    
    try:
        print("   ⏳ Generando mapa (esto puede tomar unos segundos)...")
        start_time = time.time()
        
        response = requests.get(MAP_ENDPOINT, timeout=60)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            print(f"✅ Mapa generado exitosamente en {duration:.2f} segundos")
            print(f"   - Tamaño de respuesta: {len(response.content)} bytes")
            print(f"   - Content-Type: {response.headers.get('content-type')}")
            
            # Guardar el archivo HTML
            with open("test_rutas_hotel_melia_lima.html", "wb") as f:
                f.write(response.content)
            print("   - Archivo guardado como: test_rutas_hotel_melia_lima.html")
            
            return True
        else:
            print(f"❌ Error en generación de mapa: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('detail', 'Error desconocido')}")
            except:
                print(f"   Respuesta: {response.text[:200]}...")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Timeout en la generación del mapa")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False

def check_environment():
    """Verifica la configuración del entorno"""
    print("🔧 Verificando configuración del entorno...")
    
    # Verificar API key de Google Maps
    google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if google_maps_key:
        print(f"✅ Google Maps API Key: configurada ({len(google_maps_key)} caracteres)")
    else:
        print("❌ Google Maps API Key: NO configurada")
        print("   Agrega GOOGLE_MAPS_API_KEY a tu archivo .env")
        return False
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor FastAPI: funcionando")
        else:
            print(f"⚠️  Servidor FastAPI: respondiendo con código {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ Servidor FastAPI: no disponible")
        print("   Asegúrate de que el servidor esté corriendo en http://localhost:8000")
        return False
    
    return True

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de funcionalidad de mapa de rutas")
    print("=" * 60)
    
    # Verificar entorno
    if not check_environment():
        print("\n❌ Configuración incorrecta. Revisa los errores arriba.")
        return
    
    print("\n" + "=" * 60)
    
    # Probar endpoint de estado
    status_ok = test_status_endpoint()
    
    # Probar endpoint de mapa
    mapa_ok = test_mapa_rutas_endpoint()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    if status_ok and mapa_ok:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📝 Próximos pasos:")
        print("   1. Abre test_rutas_hotel_melia_lima.html en tu navegador")
        print("   2. Verifica que el mapa se vea correctamente")
        print("   3. Revisa que las rutas estén optimizadas")
    else:
        print("❌ Algunas pruebas fallaron")
        if not status_ok:
            print("   - Endpoint de estado: FALLÓ")
        if not mapa_ok:
            print("   - Generación de mapa: FALLÓ")
        
        print("\n🔧 Posibles soluciones:")
        print("   1. Verifica que GOOGLE_MAPS_API_KEY esté configurada")
        print("   2. Asegúrate de que el servidor esté corriendo")
        print("   3. Revisa los logs del servidor para más detalles")
        print("   4. Verifica la conectividad con SheetDB")

if __name__ == "__main__":
    main() 