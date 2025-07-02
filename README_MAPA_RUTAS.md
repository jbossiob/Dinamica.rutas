# Funcionalidad de Mapa de Rutas Optimizadas

## Descripción

Esta funcionalidad permite generar rutas optimizadas automáticamente desde datos de Google Sheets, agrupar puntos geográficamente cercanos y crear un mapa interactivo con todas las rutas, partiendo desde un punto de origen configurable (por dirección o coordenadas).

## Características

- **Consumo de datos**: Obtiene datos desde Google Sheets a través de SheetDB
- **Agrupamiento geográfico**: Usa DBSCAN para agrupar puntos cercanos (0.5 km por defecto)
- **Optimización de rutas**: Utiliza Google Maps API para calcular rutas optimizadas
- **Mapa interactivo**: Genera un mapa con Folium mostrando todas las rutas
- **Endpoint REST**: Accesible vía `GET /mapa/rutas`
- **Punto de origen configurable**: Puedes usar una dirección textual o coordenadas
- **Marcador de origen destacado**: Icono de estrella azul oscuro y popup llamativo

## Estructura de Datos

### Campos requeridos en Google Sheets:
- `Latitud`: Coordenada de latitud (float)
- `Longitud`: Coordenada de longitud (float)
- `Dirección`: Dirección del punto de visita (string)
- `FechaHora`: Fecha y hora de la visita (string)

### URL de SheetDB:
```
https://sheetdb.io/api/v1/ts686wc6j3335
```

## Configuración

### Variables de Entorno Requeridas:

```bash
# API Key de Google Maps (obligatoria)
GOOGLE_MAPS_API_KEY=tu_api_key_aqui

# URL de SheetDB
API_SHEET_URL=https://sheetdb.io/api/v1/ts686wc6j3335

# Punto de origen (elige UNA de las siguientes opciones):
# Opción 1: Dirección textual (recomendado para mayor exactitud)
HOTEL_MELIA_LIMA_DIRECCION=Av. Salaverry 2599, San Isidro, Lima, Perú

# Opción 2: Coordenadas (latitud,longitud)
HOTEL_MELIA_LIMA_COORDS=-12.0926987,-77.0552319

# Configuración de CORS
CORS_ORIGINS=https://make.powerapps.com,https://apps.powerapps.com
```

> **Recomendación:** Si defines ambas (`HOTEL_MELIA_LIMA_DIRECCION` y `HOTEL_MELIA_LIMA_COORDS`), el sistema usará la dirección textual para mayor precisión visual.

### Configuración por Defecto:
- **Punto de salida**: Hotel Meliá Lima (por dirección o coordenadas)
- **Distancia de agrupamiento**: 0.5 km
- **Modo de transporte**: Conducción (driving)
- **Optimización**: Habilitada (optimize_waypoints=True)

## Endpoints

### 1. Generar Mapa de Rutas
```
GET /mapa/rutas
```

**Descripción**: Genera y retorna un mapa HTML interactivo con todas las rutas optimizadas.

**Respuesta**: Archivo HTML del mapa interactivo.

**Códigos de respuesta**:
- `200`: Mapa generado exitosamente
- `503`: Error en servicio externo (Google Sheets, Google Maps)
- `500`: Error interno del servidor

### 2. Estado del Servicio
```
GET /mapa/status
```

**Descripción**: Verifica el estado del servicio y la configuración.

**Respuesta**:
```json
{
    "status": "operativo",
    "configuracion": {
        "google_maps_api_key": "configurada",
        "sheetdb_url": "https://sheetdb.io/api/v1/ts686wc6j3335",
        "hotel_melia_lima_direccion": "Av. Salaverry 2599, San Isidro, Lima, Perú",
        "hotel_melia_lima_coords": "-12.0926987,-77.0552319",
        "distancia_agrupamiento_km": 0.5
    },
    "sheetdb_status": "conectado",
    "mensaje": "Servicio de mapas disponible"
}
```

## Flujo de Procesamiento

1. **Obtención de datos**: Se consume la API de SheetDB
2. **Validación**: Se validan y convierten los registros a puntos de visita
3. **Agrupamiento**: Se agrupan puntos cercanos usando DBSCAN
4. **Optimización**: Se calculan rutas optimizadas para cada grupo, partiendo del punto de origen
5. **Generación de mapa**: Se crea un mapa interactivo con Folium
6. **Entrega**: Se retorna el archivo HTML del mapa

## Archivos del Sistema

### Servicios:
- `app/services/mapa_rutas.py`: Lógica principal del servicio

### Routers:
- `app/routers/mapa.py`: Endpoints de la API

### Configuración:
- `app/core/config.py`: Configuraciones del sistema

## Dependencias

### Nuevas dependencias agregadas:
```
folium==0.15.1
googlemaps==4.10.0
numpy==1.24.3
scikit-learn==1.3.0
```

### Dependencias existentes utilizadas:
```
requests==2.32.4
fastapi==0.115.12
```

## Manejo de Errores

### Errores de Servicios Externos:
- **Google Sheets**: Timeout, datos inválidos, errores de red
- **Google Maps**: API key inválida, límites de cuota, errores de geocodificación

### Errores de Datos:
- Coordenadas fuera de rango válido
- Campos faltantes en registros
- Datos malformados

### Logging:
- Todos los errores se registran con logging detallado
- Información de progreso del proceso
- Advertencias para datos inválidos

## Ejemplo de Uso

### 1. Verificar estado del servicio:
```bash
curl http://localhost:8000/mapa/status
```

### 2. Generar mapa de rutas:
```bash
curl http://localhost:8000/mapa/rutas -o rutas_hotel_melia_lima.html
```

### 3. Abrir en navegador:
```bash
# En Windows
start rutas_hotel_melia_lima.html

# En Linux/Mac
open rutas_hotel_melia_lima.html
```

## Características del Mapa

### Elementos visuales:
- **Punto de salida**: Marcador azul oscuro con estrella y popup destacado en Hotel Meliá Lima
- **Puntos de visita**: Marcadores de colores por grupo
- **Rutas optimizadas**: Líneas de colores diferenciadas por grupo
- **Popups informativos**: Información de dirección y fecha

### Interactividad:
- Zoom y pan del mapa
- Información al hacer clic en marcadores
- Leyenda visual por colores de grupos

## Notas Técnicas

### Algoritmo de Agrupamiento:
- **DBSCAN**: Density-Based Spatial Clustering of Applications with Noise
- **Distancia**: 0.5 km (convertida a grados para el algoritmo)
- **Min_samples**: 1 (cada punto puede formar su propio grupo)

### Optimización de Rutas:
- **Origen**: Hotel Meliá Lima (por dirección o coordenadas)
- **Waypoints**: Puntos del grupo
- **Optimización**: Habilitada para minimizar distancia total
- **Modo**: Conducción (driving)

### Rendimiento:
- Timeout de 30 segundos para SheetDB
- Procesamiento asíncrono de grupos
- Cache de archivo HTML generado

## Recomendaciones

- **Usa la dirección textual para el origen** si quieres máxima precisión visual en el mapa.
- Si la dirección no es válida o no se puede geocodificar, el sistema usará las coordenadas como respaldo.
- Puedes personalizar el popup y el icono del marcador de origen en el archivo `mapa_rutas.py`.

---

## ¿Cómo usar el sistema? (Flujo para el usuario final)

1. **Selecciona tu ubicación:**  
   Abre en tu navegador:
   [http://localhost:8000/static/seleccion_ubicacion.html](http://localhost:8000/static/seleccion_ubicacion.html)
   - Elige tu punto en el mapa (puedes buscar, hacer clic o usar los botones de zonas rápidas).
   - Haz clic en "Enviar Ubicación" para guardar tu selección en Google Sheets.

2. **Genera y visualiza el mapa de rutas:**  
   Abre en tu navegador:
   [http://localhost:8000/mapa/rutas](http://localhost:8000/mapa/rutas)
   - Se generará y mostrará el archivo HTML interactivo con todas las rutas optimizadas y los puntos enviados por los usuarios.
   - El punto de origen (Hotel Meliá Lima) estará destacado con una estrella azul oscuro.

3. **(Opcional) Descarga o comparte el archivo generado:**  
   El archivo `rutas_hotel_melia_lima.html` se puede descargar o abrir directamente desde el navegador para compartirlo o visualizarlo en cualquier momento.

---

**Resumen visual del flujo:**

1. El usuario selecciona y envía su ubicación desde el frontend.
2. El backend genera el mapa de rutas optimizadas con todos los puntos almacenados.
3. El usuario visualiza el mapa interactivo con rutas y puntos destacados.

---

¿Dudas o sugerencias? ¡Contácta al desarrollador del sistema para soporte o mejoras! 