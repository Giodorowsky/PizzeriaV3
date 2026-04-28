import flet as ft
import asyncio
from datos_negocio import (
    COLOR_FONDO, COLOR_PRIMARIO, COLOR_TEXTO, COLOR_CONTRASTE, 
    COLOR_EXITO, COLOR_TRES, COLOR_NUEVO,
    ESTADO_PREPARANDO, ESTADO_LISTO, ESTADO_EN_CAMINO, ESTADO_ENTREGADO,
    SERVICIO_DOMICILIO
)
from views.componentes.botones import BotonAnimado

class HistorialView(ft.Container):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.expand = True
        self.bgcolor = COLOR_FONDO
        self.padding = 20

        # --- BLINDAJE CONTRA EL ERROR 'super' object has no attribute '__getattr__' ---
        # Flet exige que todas las variables de instancia existan desde el inicio
        self.vista_activa = False
        self.config = None

        # Lista de desplazamiento para los pedidos
        self.lista_pedidos = ft.ListView(expand=True, spacing=15)

        self.content = ft.Column(
            controls=[
                ft.Text("CONTROL DE PEDIDOS", size=26, weight="bold", color=COLOR_PRIMARIO),
                ft.Divider(height=20, color=ft.Colors.GREY_800),
                self.lista_pedidos, 
                ft.Container(height=10),
                BotonAnimado("ACTUALIZAR LISTA", on_click=self.cargar_pedidos_manualmente, width=250)
            ]
        )

    def will_unmount(self):
        """Se ejecuta automáticamente al salir de la pantalla para detener procesos."""
        self.vista_activa = False

    def did_mount(self):
        """Se inicia al entrar a la vista; activa el bucle de tiempo real."""
        self.vista_activa = True
        
        # Recuperamos la configuración de marca blanca de forma segura
        try:
            self.config = self.page.session.store.get("config")
        except Exception:
            self.config = None
            
        asyncio.create_task(self.bucle_refresco())

    async def bucle_refresco(self):
        """Mantiene la lista actualizada cada 10 segundos con protección anti-crash."""
        while self.vista_activa:
            try:
                await self.cargar_pedidos()
                await asyncio.sleep(10)
            except Exception:
                # Si la vista se destruye durante la espera, salimos del bucle en paz
                break

    async def cargar_pedidos_manualmente(self, e):
        """Disparador para el botón de actualización manual."""
        await self.cargar_pedidos()

    async def cargar_pedidos(self, e=None):
        """Consulta la base de datos y dibuja las tarjetas modulares."""
        self.lista_pedidos.controls.clear()
        
        # Consultamos los pedidos del turno actual (Corte 0)
        pedidos = await self.db.obtener_historial_pedidos()
        
        # Obtenemos los colores institucionales para las tarjetas
        colores = self.config.obtener("tema") if self.config else {}

        if not pedidos:
            self.lista_pedidos.controls.append(
                ft.Text("No hay pedidos registrados en este turno.", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for pedido in pedidos:
                # Usamos la clase POO TarjetaPedidoHistorial definida en componentes.py
                from views.componentes.tarjetas import TarjetaPedidoHistorial
                tarjeta = TarjetaPedidoHistorial(pedido, self.abrir_modal_detalle, colores)
                self.lista_pedidos.controls.append(tarjeta)

        # BLINDAJE ASÍNCRONO: Intentamos actualizar. Si el usuario ya cambió de pantalla, ignoramos el error.
        try:
            self.update()
        except Exception:
            pass

    def abrir_modal_detalle(self, pedido, e):
        """Abre el diálogo de gestión con flujo de estados para pedidos."""
        page = e.page if e else self.page
        if not page: return

        # 1. Procesar la lista de productos y sus sabores para el cuerpo del mensaje
        lista_productos = []
        for prod in pedido.get('detalle', []):
            sabores = ", ".join(prod.get('sabores', []))
            lista_productos.append(
                ft.Text(f"• {prod.get('nombre', '')} ({sabores})", color=COLOR_TEXTO, size=16)
            )

        # 2. Construcción de la información del cliente
        contenido_modal = [
            ft.Text("PRODUCTOS:", weight="bold", color=COLOR_PRIMARIO),
            *lista_productos,
            ft.Divider(color=ft.Colors.GREY_800),
            
            ft.Text("INFORMACIÓN DEL CLIENTE:", weight="bold", color=COLOR_PRIMARIO),
            ft.Text(f"Nombre: {pedido.get('cliente', 'General')}", color=COLOR_TEXTO),
            ft.Text(f"Teléfono: {pedido.get('tel', 'No registrado')}", color=COLOR_TEXTO),
            ft.Text(f"Dirección: {pedido.get('dir', 'N/A')}", color=COLOR_TEXTO),
            ft.Text(f"Repartidor: {pedido.get('repartidor') or 'No asignado'}", color=COLOR_NUEVO, weight="bold"),
            
            ft.Divider(color=ft.Colors.GREY_800),
            ft.Text(f"TOTAL: ${pedido.get('total', 0.0):.2f}", size=24, weight="bold", color=COLOR_EXITO),
        ]

        # 3. Campo de repartidor (Solo para pedidos a domicilio)
        input_repartidor = None
        if pedido.get('tipo') == SERVICIO_DOMICILIO:
            input_repartidor = ft.TextField(label="Asignar/Cambiar Repartidor", border_color=COLOR_PRIMARIO, height=55)
            contenido_modal.append(ft.Container(height=10))
            contenido_modal.append(input_repartidor)

        # 4. Creación del Diálogo
        dialogo = ft.AlertDialog(
            bgcolor=COLOR_FONDO,
            title=ft.Text(f"TICKET #{pedido.get('id', '')}", color=COLOR_PRIMARIO, weight="bold"),
            content=ft.Column(contenido_modal, tight=True, spacing=5, scroll=ft.ScrollMode.ADAPTIVE),
        )

        def cerrar_modal(e):
            dialogo.open = False
            page.update()

        # 5. Lógica de botones de acción según el estatus actual
        acciones = []
        if input_repartidor:
            acciones.append(
                ft.TextButton("ASIGNAR REPARTIDOR", icon=ft.Icons.MOTORCYCLE, 
                    on_click=lambda _: asyncio.create_task(self.asignar_repartidor_db(pedido['id'], input_repartidor.value, dialogo, page)))
            )

        if pedido.get('estatus') == ESTADO_LISTO:
            if pedido.get('tipo') == SERVICIO_DOMICILIO:
                acciones.insert(0, ft.TextButton("ENVIAR (EN CAMINO)", icon=ft.Icons.MOTORCYCLE, icon_color=COLOR_NUEVO,
                    on_click=lambda _: asyncio.create_task(self.actualizar_estatus(pedido['id'], ESTADO_EN_CAMINO, dialogo, page))))
            else:
                acciones.insert(0, ft.TextButton("ENTREGAR PEDIDO", icon=ft.Icons.CHECK, icon_color=COLOR_EXITO,
                    on_click=lambda _: asyncio.create_task(self.actualizar_estatus(pedido['id'], ESTADO_ENTREGADO, dialogo, page))))
        
        elif pedido.get('estatus') == ESTADO_EN_CAMINO and pedido.get('tipo') == SERVICIO_DOMICILIO:
            acciones.insert(0, ft.TextButton("MARCAR ENTREGADO", icon=ft.Icons.CHECK, icon_color=COLOR_EXITO,
                on_click=lambda _: asyncio.create_task(self.actualizar_estatus(pedido['id'], ESTADO_ENTREGADO, dialogo, page))))

        acciones.append(ft.TextButton("Cerrar", icon_color=ft.Colors.RED, on_click=cerrar_modal))
        dialogo.actions = acciones
        
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()

    async def actualizar_estatus(self, pedido_id, nuevo_estatus, dialogo, page):
        """Actualiza la base de datos y refresca la interfaz."""
        await self.db.actualizar_estatus_pedido(pedido_id, nuevo_estatus)
        dialogo.open = False
        page.update()
        await self.cargar_pedidos()
        
        # 1. Eliminamos el 'page.session.get'
        # 2. Importamos nuestra herramienta modular
        from views.componentes.ayuditas import notificar_seguro
        
        # 3. Lanzamos la notificación directamente
        notificar_seguro(page, f"✅ Ticket #{pedido_id} actualizado", COLOR_EXITO)
            
    async def asignar_repartidor_db(self, pedido_id, nombre_repartidor, dialogo, page):
        """Vincula un repartidor al pedido de domicilio."""
        if not nombre_repartidor: return
        await self.db.actualizar_repartidor_pedido(pedido_id, nombre_repartidor)
        dialogo.open = False
        page.update()
        await self.cargar_pedidos()
        
        # Usamos exactamente la misma lógica limpia aquí
        from views.componentes.ayuditas import notificar_seguro
        notificar_seguro(page, f"🛵 Repartidor asignado: {nombre_repartidor}", COLOR_NUEVO)