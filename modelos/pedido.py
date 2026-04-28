from dataclasses import dataclass, field
from datetime import datetime
from datos_negocio import ESTADO_RECIBIDO

@dataclass
class Pedido:
    # Datos de Identificación (Mantenemos el nombre original intacto para la DB)
    id_ticket: int = None
    fecha: datetime = field(default_factory=datetime.now)
    
    # Datos del Cliente 
    cliente_nombre: str = ""
    cliente_tel: str = ""
    cliente_dir: str = ""
    cliente_ref: str = ""
    
    # Lógica de Venta
    tipo_servicio: str = "" # LOCAL o DOMICILIO
    productos: list = field(default_factory=list)
    total: float = 0.0
    metodo_pago: str = ""
    estatus: str = ESTADO_RECIBIDO
    repartidor: str = ""

    # --- SOLUCIÓN POO: DECORADORES DE PROPIEDAD ---
    # Actúan como un puente invisible. Flet pide "id", pero en realidad lee/escribe "id_ticket"
    
    @property
    def id(self):
        """Getter: Devuelve el id_ticket cuando las vistas gráficas piden el .id"""
        return self.id_ticket

    @id.setter
    def id(self, valor):
        """Setter: Si el sistema intenta guardar un .id, lo guardamos en id_ticket"""
        self.id_ticket = valor

    def calcular_total(self):
        """Suma automáticamente el precio de todos los productos."""
        self.total = sum(p.precio for p in self.productos)