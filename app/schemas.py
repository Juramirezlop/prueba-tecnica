from typing import Optional
from pydantic import BaseModel

class SecopForm(BaseModel):
    referencia: str
    pais: Optional[str] = None
    entidad_estatal: Optional[str] = None
    descripcion: Optional[str] = None
    fase_actual: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    fecha_presentacion_ofertas: Optional[str] = None
    url_detalle: Optional[str] = None

class CC2026Form(BaseModel):
    radicacion: str
    numero: Optional[str] = None
    ponente: Optional[str] = None
    norma_demandada: Optional[str] = None
    demandante: Optional[str] = None
    fecha: Optional[str] = None
    url_proceso: Optional[str] = None
    url_demanda: Optional[str] = None
    capture_date: Optional[str] = None
