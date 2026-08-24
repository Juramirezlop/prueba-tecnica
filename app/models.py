"""
Modelos de base de datos:
- usuarios: cuentas de acceso con rol (administrador, digitador, consulta).
- secop: datos depurados de la hoja SECOP. Llave de negocio: referencia.
- cc2026: datos depurados de la hoja CC2026. Llave de negocio: radicacion.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False)

class Secop(Base):
    __tablename__ = "secop"

    id = Column(Integer, primary_key=True, index=True)
    referencia = Column(String(255), unique=True, nullable=False, index=True)
    pais = Column(String(100))
    entidad_estatal = Column(Text)
    descripcion = Column(Text)
    fase_actual = Column(String(255))
    fecha_publicacion = Column(String(255))
    fecha_presentacion_ofertas = Column(String(255))
    url_detalle = Column(Text)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

class CC2026(Base):
    __tablename__ = "cc2026"

    id = Column(Integer, primary_key=True, index=True)
    radicacion = Column(String(255), unique=True, nullable=False, index=True)
    numero = Column(String(50))
    ponente = Column(String(255))
    norma_demandada = Column(Text)
    demandante = Column(Text)
    fecha = Column(String(255))
    url_proceso = Column(Text)
    url_demanda = Column(Text)
    capture_date = Column(String(255))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())