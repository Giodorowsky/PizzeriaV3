import flet as ft
import asyncio
# Respetamos estrictamente tus constantes y componentes definidos
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE
from views.componentes.botones import BotonAnimado

class StatsView(ft.Container):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        # Cuadrícula responsiva para las tarjetas de métricas
        self.grid_stats = ft.ResponsiveRow(spacing=15, run_spacing=15)

        self.content = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=10),
                ft.Text("DASHBOARD EMPRESARIAL", size=26, weight="bold", color=COLOR_PRIMARIO),
                ft.Text("Rendimiento del turno actual", color=ft.Colors.GREY_400, size=14),
                ft.Divider(height=30, color=ft.Colors.GREY_800),
                
                # Inyección dinámica de métricas
                self.grid_stats,
                
                ft.Container(height=30),
                BotonAnimado(
                    "ACTUALIZAR MÉTRICAS", 
                    on_click=self.actualizar_metricas_manualmente, 
                    width=280, 
                    bgcolor=COLOR_CONTRASTE
                ),
                ft.Container(height=20),
            ]
        )

    def _crear_kpi(self, titulo, valor, icono, color_icono, col_size=6):
        """Genera una tarjeta de métrica profesional para la cuadrícula"""
        return ft.Container(
            col={"xs": col_size, "sm": 4},
            bgcolor="#1E1E1E", 
            padding=15, 
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.with_opacity(0.1, "black")),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Icon(icono, color=color_icono, size=28),
                    ft.Text(valor, size=20, weight="bold", color=COLOR_TEXTO),
                    ft.Text(titulo, size=10, color=ft.Colors.GREY_500, weight="bold"),
                ], 
                spacing=5
            )
        )

    def did_mount(self):
        """Carga automática al deslizar hacia la vista"""
        asyncio.create_task(self.cargar_datos_financieros(None))

    async def actualizar_metricas_manualmente(self, e):
        await self.cargar_datos_financieros(e)

    async def cargar_datos_financieros(self, e):
        """Consulta la base de datos y dibuja el desglose profesional"""
        try:
            # Indicador de carga
            self.grid_stats.controls = [ft.ProgressRing(color=COLOR_PRIMARIO)]
            self.update() # Refresco síncrono para evitar errores de NoneType

            # Obtenemos el resumen con el nuevo cálculo de neto_efectivo
            data = await self.db.obtener_resumen_dia() 
            
            self.grid_stats.controls = [
                # BLOQUE 1: Efectivo (Lo más importante para el dueño)
                self._crear_kpi("NETO EN CAJA", f"${data.get('neto_efectivo', 0.0):,.2f}", ft.Icons.ACCOUNT_BALANCE_WALLET, ft.Colors.GREEN_ACCENT, col_size=12),
                
                # BLOQUE 2: Desglose de Ventas
                self._crear_kpi("VENTAS TOTALES", f"${data.get('total', 0.0):,.2f}", ft.Icons.MONETIZATION_ON, ft.Colors.GREEN),
                self._crear_kpi("GASTOS", f"${data.get('gastos', 0.0):,.2f}", ft.Icons.OUTBOND, ft.Colors.RED),
                
                # BLOQUE 3: Métodos de Pago
                self._crear_kpi("EFECTIVO BRUTO", f"${data.get('efectivo', 0.0):,.2f}", ft.Icons.PAYMENTS_OUTLINED, ft.Colors.BLUE),
                self._crear_kpi("TARJETA", f"${data.get('tarjeta', 0.0):,.2f}", ft.Icons.CREDIT_CARD, ft.Colors.PURPLE),
                
                # BLOQUE 4: Operatividad
                self._crear_kpi("LOCAL", f"{data.get('local', 0)} tickets", ft.Icons.RESTAURANT, ft.Colors.AMBER),
                self._crear_kpi("DOMICILIO", f"{data.get('domicilio', 0)} tickets", ft.Icons.DELIVERY_DINING, ft.Colors.ORANGE),
            ]
            
            self.update()
            
        except Exception as ex:
            print(f"Error en stats_view: {ex}")
            self.grid_stats.controls = [ft.Text("Error al cargar datos", color=ft.Colors.RED)]
            self.update()