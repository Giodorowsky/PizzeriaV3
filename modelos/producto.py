from dataclasses import dataclass, field
from typing import List

@dataclass
class Producto:
    nombre: str
    precio: float
    limite_sabores: int  # Ahora es obligatorio definirlo al crear la pizza
    es_promo: bool = False
    sabores_elegidos: List[str] = field(default_factory=list)
    incluye_refresco: bool = False
    refresco_elegido: str = None

    def puede_agregar_sabor(self) -> bool:
        """Verifica si todavía hay espacio para más sabores."""
        return len(self.sabores_elegidos) < self.limite_sabores

    def agregar_sabor(self, sabor: str):
        """Agrega el sabor a la lista interna del objeto."""
        if self.puede_agregar_sabor():
            self.sabores_elegidos.append(sabor)
            return True
        return False