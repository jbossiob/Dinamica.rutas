from pydantic import BaseModel
from typing import List, Dict, Optional

# estructura de los datos que se van a enviar a la API
class PuntoVisita(BaseModel):
    id_pc: str  # Cambiado de int a str para coincidir con codigodece
    nombre: str
    lat: float
    long: float
    poblacion: int
    cont_avenida: Optional[int] = None
    cont_estiaje: Optional[int] = None
    cant_lect_metales: Optional[int] = None
    sistema_cloro: Optional[bool] = None
    cant_decla_emerg: Optional[int] = None
    pob_menor_12: Optional[int] = None
    cant_est_salud: Optional[int] = None
    cant_est_edu: Optional[int] = None
    conflic_alrededor: Optional[int] = None
    prioridad: Optional[float] = None

class SeleccionRequest(BaseModel):
    id_analista: int
    codigos_pc: List[str]

class SeleccionActividadRequest(BaseModel):
    id_analista: int
    actividades_por_punto: Dict[str, List[int]]  # Ejemplo: {"2001140036": [1, 2], "2001140068": [3]}

class PuntoRuta(BaseModel):
    codigodece: str
    orden_visita: int
    dia_ruta: int
    prioridad: float | None
    tiempo_estimado_min: float | None
    distancia_km: float | None

class RutaGenerada(BaseModel):
    id: int
    fecha_generacion: str
    duracion_total_min: float
    distancia_total_km: float
    prioridad_total: float
    puntos: List[PuntoRuta]