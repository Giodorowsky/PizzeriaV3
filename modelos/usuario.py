from dataclasses import dataclass

@dataclass
class Usuario:
    nombre: str
    rol: str  # Ejemplo: 'Cajero', 'Cocinero', 'Dueño'
    esta_activo: bool