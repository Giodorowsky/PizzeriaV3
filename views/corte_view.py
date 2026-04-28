import flet as ft
import asyncio
# Respetamos tus constantes y componentes definidos
from datos_negocio import COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE, COLOR_EXITO, COLOR_ERROR
from views.componentes.botones import BotonAnimado

class CorteView(ft.Container):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        # Variables de texto para el desglose financiero
        self.txt_ventas_total = ft.Text("$0.00", color=COLOR_TEXTO, size=16, weight="bold")
        self.txt_ventas_tarjeta = ft.Text("$0.00", color=ft.Colors.PURPLE_300, size=16)
        self.txt_ventas_efectivo = ft.Text("$0.00", color=ft.Colors.GREEN_300, size=16)
        self.txt_gastos = ft.Text("-$0.00", color=ft.Colors.RED_400, size=16)
        
        # El dato más importante para el dueño
        self.txt_neto_entregar = ft.Text("$0.00", color=COLOR_EXITO, size=28, weight="bold")

        # Diseño tipo Recibo/Ticket
        self.tarjeta_corte = ft.Container(
            bgcolor=COLOR_CONTRASTE,
            padding=25,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.2, "black")),
            content=ft.Column([
                self._crear_fila("Ventas Totales:", self.txt_ventas_total),
                ft.Divider(height=10, color=ft.Colors.GREY_800),
                self._crear_fila("Cobros con Tarjeta:", self.txt_ventas_tarjeta),
                self._crear_fila("Cobros en Efectivo:", self.txt_ventas_efectivo),
                self._crear_fila("Gastos del Turno:", self.txt_gastos),
                ft.Divider(height=20, color=COLOR_PRIMARIO),
                ft.Column([
                    ft.Text("EFECTIVO NETO A ENTREGAR:", size=14, color=COLOR_PRIMARIO, weight="bold"),
                    self.txt_neto_entregar,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
            ], spacing=12)
        )

        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Container(height=10),
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=50, color=COLOR_PRIMARIO),
                ft.Text("CORTE DE CAJA", size=24, weight="bold", color=COLOR_PRIMARIO),
                ft.Text("Balance de efectivo físico", color=ft.Colors.GREY_400, size=14),
                ft.Container(height=20),
                
                self.tarjeta_corte,
                
                ft.Container(height=30),
                BotonAnimado("FINALIZAR DÍA", on_click=self.abrir_confirmacion, bgcolor=ft.Colors.RED_700, width=280),
                ft.Container(height=10),
                BotonAnimado("ACTUALIZAR DATOS", on_click=self.cargar_datos_corte, width=280, bgcolor=COLOR_CONTRASTE)
            ]
        )

    def _crear_fila(self, etiqueta, control_valor):
        return ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(etiqueta, size=15, color=ft.Colors.GREY_300),
                control_valor
            ]
        )

    def did_mount(self):
        # Carga automática al entrar a la vista
        asyncio.create_task(self.cargar_datos_corte(None))

    async def cargar_datos_corte(self, e):
        """Consulta la BD y actualiza el desglose financiero"""
        try:
            # Usamos el método que separa efectivo de tarjeta en database.py
            resumen = await self.db.obtener_resumen_dia() 
            
            self.txt_ventas_total.value = f"${resumen.get('total', 0.0):,.2f}"
            self.txt_ventas_tarjeta.value = f"${resumen.get('tarjeta', 0.0):,.2f}"
            self.txt_ventas_efectivo.value = f"${resumen.get('efectivo', 0.0):,.2f}"
            self.txt_gastos.value = f"-${resumen.get('gastos', 0.0):,.2f}"
            
            # El neto ya viene calculado desde el Manager: (Efectivo - Gastos)
            self.txt_neto_entregar.value = f"${resumen.get('neto_efectivo', 0.0):,.2f}"
            
            self.update() # Refresco síncrono para evitar errores de NoneType en 0.84.0
        except Exception as ex:
            print(f"Error en cargar_datos_corte: {ex}")

    async def abrir_confirmacion(self, e):
        # Función segura para cerrar en Android
        def cerrar_dialogo(e):
            dialogo.open = False
            self.page.update()

        dialogo = ft.AlertDialog(
            bgcolor=COLOR_FONDO,
            title=ft.Text("Confirmar Cierre", color=ft.Colors.RED_400, weight="bold"),
            content=ft.Text("¿Estás seguro de finalizar el día? Se archivarán las ventas actuales y la caja volverá a cero."),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo), # <-- CORREGIDO
                ft.TextButton("SÍ, CERRAR", on_click=lambda _: asyncio.create_task(self.ejecutar_cierre(dialogo)), style=ft.ButtonStyle(color=ft.Colors.RED_400))
            ]
        )
        self.page.overlay.append(dialogo)
        dialogo.open = True
        self.page.update()
    async def ejecutar_cierre(self, dialogo):
        try:
            await self.db.cerrar_dia_operativo()
            dialogo.open = False
            self.page.update()
            
            # Notificación visual
            lanzar_alerta = self.page.session.store.get("notificar")
            if lanzar_alerta:
                lanzar_alerta("Corte realizado correctamente", COLOR_EXITO)
            
            # Limpiar la vista
            await self.cargar_datos_corte(None)
            self.page.update()
        except Exception as ex:
            lanzar_alerta = self.page.session.store.get("notificar")
            if lanzar_alerta:
                lanzar_alerta("Error", COLOR_ERROR)
            