from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Analista(Base):
    __tablename__ = "analista"
    id_analista = Column(Integer, primary_key=True)
    nombre = Column(String)

class CentroPoblado(Base):
    __tablename__ = "centro_poblado"

    codigodece = Column(String, primary_key=True)
    nombre = Column(String(100))
    poblacion = Column(Integer)
    cont_avenida = Column(Integer)
    cont_estiaje = Column(Integer)
    cant_lect_metales = Column(Integer)
    sistema_cloro = Column(Boolean)
    cant_decla_emerg = Column(Integer)
    pob_menor_12 = Column(Integer)
    cant_est_salud = Column(Integer)
    cant_est_edu = Column(Integer)
    conflic_alrededor = Column(Integer)
    latitud = Column(Float)
    longitud = Column(Float)
    id_distrito = Column(Integer, ForeignKey("distrito.id_distrito"))

class SeleccionPC(Base):
    __tablename__ = "seleccion_pc"

    id_seleccion = Column(Integer, primary_key=True, index=True)
    id_analista = Column(Integer, ForeignKey("analista.id_analista"), nullable=False)
    codigodece =  Column(String, ForeignKey("centro_poblado.codigodece"), nullable=False)
    fecha_seleccion = Column(DateTime(timezone=True), server_default=func.now())

class Actividad(Base):
    __tablename__ = "actividad"
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    duracion_min = Column(Integer)

class SeleccionActividad(Base):
    __tablename__ = "seleccion_actividad"
    id = Column(Integer, primary_key=True, index=True)
    id_analista = Column(Integer, nullable=False)
    codigodece = Column(String, nullable=False)
    id_actividad = Column(Integer, ForeignKey("actividad.id"), nullable=False)

    actividad = relationship("Actividad")

class RutasGeneradas(Base):
    __tablename__ = "rutas_generadas"

    id = Column(Integer, primary_key=True, index=True)
    id_analista = Column(Integer, nullable=False)
    fecha_generacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    duracion_total_min = Column(Float)
    distancia_total_km = Column(Float)
    prioridad_total = Column(Float)
    observaciones = Column(Text)

    puntos = relationship("HistorialRuta", back_populates="ruta", cascade="all, delete")

class HistorialRuta(Base):
    __tablename__ = "historial_ruta"

    id = Column(Integer, primary_key=True, index=True)
    id_ruta = Column(Integer, ForeignKey("rutas_generadas.id", ondelete="CASCADE"), nullable=False)
    codigodece = Column(String, nullable=False)
    orden_visita = Column(Integer, nullable=False)
    dia_ruta = Column(Integer, nullable=False)
    prioridad = Column(Float)
    tiempo_estimado_min = Column(Float)
    distancia_km = Column(Float)

    ruta = relationship("RutasGeneradas", back_populates="puntos")




