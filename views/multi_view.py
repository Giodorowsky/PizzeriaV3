import flet as ft
# Importamos las vistas que se mostrarán dentro del deslizador
from views.pos_view import PosView
from views.cocina_view import CocinaView
from views.stats_view import StatsView
from views.gastos_view import GastosView
from views.corte_view import CorteView
from views.historial_view import HistorialView

class MultiViewContainer(ft.Container):
    """
    Contenedor principal que utiliza un PageView para permitir 
    el desplazamiento lateral (swipe) entre diferentes vistas.
    """
    def __init__(self, usuario, db):
        super().__init__()
        self.usuario = usuario
        self.db = db
        self.expand = True
        
        # El PageView organiza las pantallas horizontalmente por defecto.
        # Eliminamos 'scroll_direction' para evitar el TypeError reportado.
        self.page_view = ft.PageView(
            expand=True,
            controls=self._configurar_paginas_por_rol(),
            # Animación suave para la transición entre páginas
            animate_size=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        )
        
        self.content = self.page_view

    def _configurar_paginas_por_rol(self):
        """
        Determina qué pantallas estarán disponibles para el usuario
        según el rol detectado tras ingresar el PIN.
        """
        paginas = []

        if self.usuario.rol == "DUEÑO":
            # El dueño desliza entre sus Estadísticas y el Punto de Venta
            paginas.append(StatsView(self.db))
            paginas.append(PosView(self.usuario, self.db))
            paginas.append(HistorialView( self.db)) # 3. Control de estatus
            paginas.append(CorteView(self.db))
            
        elif self.usuario.rol == "CAJERA":
            # La cajera desliza entre el Punto de Venta y el Registro de Gastos
            paginas.append(PosView(self.usuario, self.db))
            paginas.append(GastosView(self.db, self.usuario.nombre))
            paginas.append(HistorialView( self.db))
            
        elif self.usuario.rol == "COCINA":
            # El personal de cocina ve directamente el monitor de pedidos
            paginas.append(CocinaView(self.db))
            
        return paginas

    async def ir_a_pagina(self, indice):
        """
        Permite cambiar de página mediante código (por ejemplo, desde un botón).
        """
        self.page_view.page_index = indice
        # Usamos el método update() que es seguro en entornos asíncronos en 0.84.0
        await self.update()