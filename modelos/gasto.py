# modelos/gasto.py
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Gasto:
    descripcion: str
    monto: float
    cajero: str
    fecha: datetime = field(default_factory=datetime.now)