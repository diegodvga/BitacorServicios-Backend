from datetime import date
from typing import Optional
from pydantic import BaseModel

class CrearDispositivo(BaseModel):
    name: str
    apellido: str
    serial_number: str
    tipo: str
    marca: str
    modelo: str
    imei: str | None = None
    numero_linea: str | None = None
    color: str | None = None
    almacenamiento: str | None = None
    ram: str | None = None
    sistema_operativo: str | None = None
    fecha_compra: str | None = None
    estado: str | None = None
    propietario: str | None = None

class Dispositivo(BaseModel):
    serial_number: str
    tipo: str
    marca: str
    modelo: str
    imei: str | None = None
    numero_linea: str | None = None
    color: str | None = None
    almacenamiento: str | None = None
    ram: str | None = None
    sistema_operativo: str | None = None
    fecha_compra: date | None = None
    estado: str | None = None
    propietario: str | None = None
   
class ActualizarDispositivo(BaseModel):
    tipo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    imei: Optional[str] = None
    numero_linea: Optional[str] = None
    color: Optional[str] = None
    almacenamiento: Optional[str] = None
    ram: Optional[str] = None
    sistema_operativo: Optional[str] = None
    fecha_compra: Optional[date] = None
    estado: Optional[str] = None
    propietario: Optional[str] = None

    
class Servicios(BaseModel):
    serial_number: str
    fecha: str
    persona_responsable: str
    estado: str
    descripcion: str
    observaciones: str


