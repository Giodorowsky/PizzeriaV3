import flet as ft
import asyncio
#import flet_audio as fta  # Importamos el nuevo motor de sonido
from datos_negocio import (
    COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE, 
    COLOR_EXITO, COLOR_ERROR, COLOR_NUEVO, ESTADO_LISTO
)
from views.componentes.botones import BotonAnimado 

class CocinaView(ft.Container):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20
        
        self.ultimo_id_visto = 0 
        self.vista_activa = True 
        
        # 🎵 2. SOLUCIÓN NATIVA: Creamos el reproductor de audio de Flet
        #self.audio_campana = fta.Audio(src="campana.mp3", autoplay=False)
        
        self.lista_tickets = ft.ResponsiveRow(spacing=15, run_spacing=15)
        
        self.content = ft.Column(
            scroll=ft.ScrollMode.ADAPTIVE,
            controls=[
                ft.Text("MONITOR DE COCINA", size=28, weight="bold", color=COLOR_PRIMARIO),
                ft.Divider(height=10, color=ft.Colors.GREY_800),
                self.lista_tickets
            ]
        )

    def _notificar(self, mensaje, color):
        from views.componentes.ayuditas import notificar_seguro
        if getattr(self, "page", None):
            notificar_seguro(self.page, mensaje, color)

    def will_unmount(self):
        self.vista_activa = False

    def did_mount(self):
        self.vista_activa = True
        
        # 🎵 3. Agregamos el audio de forma invisible a la pantalla al abrir la cocina
        #if self.audio_campana not in self.page.overlay:
           # self.page.overlay.append(self.audio_campana)
            #self.page.update()
            
        asyncio.create_task(self.bucle_actualizacion())

    def tocar_campana_local(self):
        """Reproduce sonido de aviso usando el motor de Flet."""
        try:
            pass
            # 🎵 4. Reproducción segura sin depender de librerías externas
            #self.audio_campana.play()
        except Exception as e:
            print(f"Error de audio: {e}")

    async def bucle_actualizacion(self):
        """Monitorea la base de datos sin causar crashes."""
        while self.vista_activa:
            try:
                pedidos = await self.db.obtener_pedidos_cocina()
                
                if pedidos:
                    max_id_actual = max([p.get('id', 0) for p in pedidos]) 
                    
                    if self.ultimo_id_visto > 0 and max_id_actual > self.ultimo_id_visto:
                        self.tocar_campana_local()
                        self._notificar(f"¡NUEVO PEDIDO! Ticket #{max_id_actual}", COLOR_PRIMARIO)
                    
                    self.ultimo_id_visto = max(self.ultimo_id_visto, max_id_actual)
                
                await self.dibujar_tickets(pedidos)
                await asyncio.sleep(5) 
                
            except Exception as e:
                print(f"🔥 Error en el bucle de cocina: {e}")
                await asyncio.sleep(5)

    async def dibujar_tickets(self, pedidos):
        """Dibuja los tickets (Máximo 4) con fuentes grandes para laptop."""
        self.lista_tickets.controls.clear()
        
        for p in pedidos[:4]:
            servicio = p.get('servicio', 'LOCAL')
            es_domicilio = servicio == "DOMICILIO"
            color_etiqueta = COLOR_ERROR if es_domicilio else COLOR_NUEVO 

            lista_productos_visuales = []
            for prod in p.get('detalle', []):
                nombre_prod = prod.get('nombre', 'Producto Desconocido')
                sabores = prod.get('sabores', [])
                texto_sabores = f" ({', '.join(sabores)})" if sabores else ""
                
                lista_productos_visuales.append(
                    ft.Text(f"• {nombre_prod}{texto_sabores}", size=22, weight="w500", color=COLOR_TEXTO)
                )

            ticket = ft.Container(
                col={"md": 12}, 
                bgcolor=COLOR_CONTRASTE,
                padding=15,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, COLOR_TEXTO)),
                content=ft.Row([
                    ft.Column([
                        ft.Text(f"#{p.get('id', '?')}", size=26, weight="bold", color=COLOR_PRIMARIO),
                        ft.Container(
                            bgcolor=color_etiqueta, 
                            padding=ft.Padding.symmetric(horizontal=8, vertical=2), 
                            border_radius=5, 
                            content=ft.Text(servicio, size=10, weight="bold")
                        )
                    ], width=100, alignment=ft.MainAxisAlignment.CENTER),
                    
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                    
                    ft.Column(lista_productos_visuales, spacing=5, expand=True),
                    
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_800),
                    
                    ft.Container(
                        width=180,
                        content=BotonAnimado(
                            "LISTO", 
                            on_click=lambda _, id_p=p.get('id'): asyncio.create_task(self.marcar_listo(id_p)), 
                            bgcolor=COLOR_EXITO,
                            height=45
                        )
                    )
                ], spacing=20)
            )
            self.lista_tickets.controls.append(ticket)
            
        try:
            self.update()
        except Exception:
            pass

    async def marcar_listo(self, id_ticket):
        try: 
            await self.db.actualizar_estatus_pedido(id_ticket, ESTADO_LISTO)
            self._notificar(f"Pedido #{id_ticket} marcado como listo", COLOR_EXITO)
            
            pedidos_actualizados = await self.db.obtener_pedidos_cocina()
            await self.dibujar_tickets(pedidos_actualizados)
        except Exception as e:
            self._notificar(f"Error al procesar: {str(e)}", COLOR_ERROR)