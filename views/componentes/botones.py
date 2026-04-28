# 1. IMPORTACIONES BÁSICAS NECESARIAS PARA ESTE ARCHIVO
import flet as ft
import asyncio
import inspect
from datos_negocio import COLOR_PRIMARIO, COLOR_TEXTO

class BotonAnimado(ft.Container):
    """Botón con soporte para funciones asíncronas y lambdas."""
    def __init__(self, texto, on_click, bgcolor=COLOR_PRIMARIO, color_texto=COLOR_TEXTO, width=None, height=50, icono=None):
        super().__init__()
        self.bgcolor = bgcolor
        self.border_radius = 12
        self.width = width
        self.height = height
        self.alignment = ft.Alignment.CENTER
        self.animate_scale = ft.Animation(150, "decelerate")
        
        self.shadow = ft.BoxShadow(
            blur_radius=8, 
            color=ft.Colors.with_opacity(0.4, bgcolor), 
            offset=ft.Offset(0, 4)
        )

        if icono:
            self.content = ft.Row(
                [ft.Icon(icono, color=color_texto), ft.Text(texto, color=color_texto, weight="bold")], 
                alignment=ft.MainAxisAlignment.CENTER, 
                spacing=10
            )
        else:
            self.content = ft.Text(texto, color=color_texto, weight="bold")

        self._accion_original = on_click
        self.on_click = self._animar_y_ejecutar

    async def _animar_y_ejecutar(self, e):
        if not self.page:
            return
        
        self.scale = 0.95
        self.shadow.offset = ft.Offset(0, 1)
        self.update()
        
        await asyncio.sleep(0.1) 
        
        self.scale = 1.0
        self.shadow.offset = ft.Offset(0, 4)
        self.update()
        
        if self._accion_original:
            if inspect.iscoroutinefunction(self._accion_original):
                await self._accion_original(e)
            else:
                resultado = self._accion_original(e)
                if inspect.isawaitable(resultado):
                    await resultado

class BarraNavegacion(ft.AppBar): 
    """Barra superior de navegación."""
    def __init__(self, titulo, page, usuario=None): 
        super().__init__() 
        self.pagina_actual = page 
        self.bgcolor = COLOR_PRIMARIO 
        
        self.title = ft.Text(titulo, weight=ft.FontWeight.BOLD, color=COLOR_TEXTO, size=22)
        self.center_title = True 
        
        self.leading = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW, 
            icon_color=COLOR_TEXTO, 
            on_click=self._retroceder 
        )

    async def _retroceder(self, e): 
        if len(self.pagina_actual.views) > 1: 
            self.pagina_actual.views.pop() 
            top_view = self.pagina_actual.views[-1] 
            await self.pagina_actual.push_route(top_view.route) 
        else:
            await self.pagina_actual.push_route("/")
