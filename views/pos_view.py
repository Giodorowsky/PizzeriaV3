import flet as ft
import asyncio
from datos_negocio import *
from modelos.producto import Producto
from modelos.pedido import Pedido

# 🧹 IMPORTACIONES LIMPIAS: Eliminamos las vistas gráficas de la cabecera para 
# forzar el Lazy Loading y reducir el tiempo de arranque.

class PosView(ft.Container):
    def __init__(self, sesion, db):
        super().__init__(expand=True, bgcolor=COLOR_FONDO) # OOP: Inicialización directa en el super
        self.db = db
        self.sesion = sesion
        self.pedido_actual = Pedido()
        self.pizza_en_preparacion = None

        self.vistas_flujo = ft.Container(expand=True, padding=20, alignment=ft.Alignment.CENTER)
        self.content = self.vistas_flujo
        
        self.preparar_interfaz_inicial()

    def _mostrar_notificacion(self, mensaje, color):
        """Único canal de comunicación para alertas. Lazy Load de 'ayuditas'."""
        from views.componentes.ayuditas import notificar_seguro
        if self.page:
            notificar_seguro(self.page, mensaje, color)

    def preparar_interfaz_inicial(self):
        """Paso 1: Selección de Servicio."""
        opciones = [
            ["LOCAL", ft.Icons.RESTAURANT, SERVICIO_LOCAL, None, COLOR_NUEVO],
            ["DOMICILIO", ft.Icons.DELIVERY_DINING, SERVICIO_DOMICILIO, None, ft.Colors.RED_600]
        ]
        
        from views.componentes.tarjetas import SelectorGrid # <--- Lazy Loading correcto
        self.vistas_flujo.content = SelectorGrid(
            titulo="TIPO DE SERVICIO",
            opciones=opciones,
            al_seleccionar=self.registrar_servicio,
            columnas=1  
        )
        try: self.update()
        except: pass

    def registrar_servicio(self, valor):
        self.pedido_actual.tipo_servicio = valor
        self.mostrar_seleccion_tamano()

    def mostrar_seleccion_tamano(self):
        """Paso 2: Selección de Tamaños."""
        opciones = [
            ["CHICA", "chica.png", "CHICA", "100.00"],
            ["MEDIANA", "mediana.png", "MEDIANA", "150.00"],
            ["GRANDE", "grande.png", "GRANDE", "200.00"],
            ["FAMILIAR", "familiar.png", "FAMILIAR", "250.00"]
        ]
        
        from views.componentes.tarjetas import SelectorGrid
        from views.componentes.botones import BotonAnimado
        
        self.vistas_flujo.content = ft.Column(
            alignment="center", horizontal_alignment="center",
            controls=[
                SelectorGrid(titulo="TAMAÑO", opciones=opciones, al_seleccionar=self.iniciar_preparacion_pizza_por_nombre),
                BotonAnimado("CANCELAR", on_click=lambda _: self.preparar_interfaz_inicial(), bgcolor=COLOR_ERROR)
            ]
        )
        self.update()

    def mostrar_menu_promos(self):
        """Paso 2B: Selección de Promociones Especiales."""
        opciones = [
            # CORRECCIÓN DE ESTRUCTURA: [Nombre, Icono, Valor, Precio]
            [nombre, ft.Icons.LOCAL_OFFER, nombre, PRECIOS_PIZZAS[nombre][0]] 
            for nombre in ["BARRA", "MEGA"]
        ]
        
        from views.componentes.tarjetas import SelectorGrid
        from views.componentes.botones import BotonAnimado
        
        self.vistas_flujo.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
            controls=[
                SelectorGrid("PROMOCIONES", opciones, self.iniciar_preparacion_pizza_por_nombre),
                ft.Text("¡Estas pizzas incluyen refresco gratis!", size=16, color=COLOR_EXITO, italic=True),
                ft.Container(height=10),
                BotonAnimado("VOLVER A TAMAÑOS", on_click=lambda _: self.mostrar_seleccion_tamano(), bgcolor=COLOR_SECUNDARIO)
            ]
        )
        self.update()

    def iniciar_preparacion_pizza_por_nombre(self, nombre):
        info = PRECIOS_PIZZAS[nombre]
        self.iniciar_preparacion_pizza(nombre, info)

    def iniciar_preparacion_pizza(self, nombre, info):
        self.pizza_en_preparacion = Producto(nombre, info[0], info[1], info[2])
        self.mostrar_seleccion_sabores()

    def mostrar_seleccion_sabores(self):
        """Paso 3: Selección de Sabores con diseño de 2 columnas y scroll para Android."""
        # 1. Título dinámico que muestra cuántos sabores faltan por elegir
        titulo = f"SABORES ({len(self.pizza_en_preparacion.sabores_elegidos)}/{self.pizza_en_preparacion.limite_sabores})"
        
        # 2. Generamos la lista de opciones (Nombre, Imagen compartida, Valor)
        # Nota: Usamos 'sabor.png' como imagen estándar para todos los ingredientes
        opciones_sabores = [[sabor, "sabor.png", sabor] for sabor in SABORES_CATALOGO]

        # 3. Importaciones diferidas (Lazy Loading) para mantener la app ligera en RAM
        from views.componentes.tarjetas import SelectorGrid
        from views.componentes.botones import BotonAnimado
        
        # 4. Actualizamos el contenido principal con el modo de desplazamiento (Scroll)
        self.vistas_flujo.content = ft.Column(
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.ADAPTIVE, # Crucial para que los botones grandes no se corten
            controls=[
                # Configuramos 2 columnas para maximizar el tamaño de los botones táctiles
                SelectorGrid(
                    titulo=titulo, 
                    opciones=opciones_sabores, 
                    al_seleccionar=self.agregar_sabor, 
                    columnas=2
                ),
                ft.Container(height=20),
                BotonAnimado(
                    "CANCELAR PIZZA", 
                    on_click=lambda _: self.mostrar_seleccion_tamano(), 
                    bgcolor=COLOR_ERROR,
                    width=300
                )
            ]
        )
        
        # 5. Refrescamos la vista para aplicar los cambios visuales
        self.update()
        
    def agregar_sabor(self, sabor):
        if self.pizza_en_preparacion.agregar_sabor(sabor):
            if not self.pizza_en_preparacion.puede_agregar_sabor():
                if self.pizza_en_preparacion.incluye_refresco:
                    self.mostrar_seleccion_refresco()
                else:
                    self.finalizar_pizza_individual()
            else:
                self.mostrar_seleccion_sabores()

    def mostrar_seleccion_refresco(self):
        """Paso 4: Selección de Refresco."""
        refrescos = ["COCA COLA", "SPRITE", "SIDRAL", "MANZANITA"]
        # CORRECCIÓN DE ESTRUCTURA: Convertimos la lista de textos a matrices compatibles
        opciones_refrescos = [[r, ft.Icons.LOCAL_DRINK, r] for r in refrescos]
        
        from views.componentes.tarjetas import SelectorGrid
        self.vistas_flujo.content = SelectorGrid("REFRESCO GRATIS", opciones_refrescos, self.set_refresco, 2)
        self.update()

    def set_refresco(self, sabor_ref):
        self.pizza_en_preparacion.refresco_elegido = sabor_ref
        self.finalizar_pizza_individual()

    def finalizar_pizza_individual(self):
        """Paso 5: Resumen y opciones de continuación."""
        self.pedido_actual.productos.append(self.pizza_en_preparacion)
        self.pedido_actual.calcular_total()
        
        from views.componentes.botones import BotonAnimado
        self.vistas_flujo.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20,
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=COLOR_EXITO, size=80),
                ft.Text("¡AGREGADO!", size=28, weight="bold"),
                ft.Text(f"Total Carrito: ${self.pedido_actual.total}", size=22, color=COLOR_TEXTO),
                ft.Container(height=10),
                BotonAnimado("AGREGAR OTRA PIZZA", on_click=lambda _: self.mostrar_seleccion_tamano(), bgcolor=COLOR_CONTRASTE, width=300),
                BotonAnimado("FINALIZAR Y PAGAR", on_click=lambda _: self.mostrar_formulario_cliente(), bgcolor=COLOR_PRIMARIO, width=300)
            ]
        )
        self.update()

    def mostrar_formulario_cliente(self):
        """Paso 6: Formulario de envío."""
        from views.componentes.formularios import FormularioEntrega
        self.vistas_flujo.content = FormularioEntrega(
            es_domicilio=(self.pedido_actual.tipo_servicio == SERVICIO_DOMICILIO),
            al_finalizar=self.validar_y_pagar
        )
        self.update()

    def validar_y_pagar(self, formulario):
        datos = formulario.obtener_datos()
        if not datos["nombre"]:
            self._mostrar_notificacion("El nombre del cliente es obligatorio", COLOR_ERROR)
            return
            
        self.pedido_actual.cliente_nombre = datos["nombre"]
        self.pedido_actual.cliente_tel = datos["tel"]
        self.pedido_actual.cliente_dir = datos["dir"]
        self.pedido_actual.cliente_ref = datos["ref"]
        self.mostrar_pantalla_pago()

    def mostrar_pantalla_pago(self):
        """Paso 7: Pantalla de Pago y Guardado final."""
        from views.componentes.botones import BotonAnimado
        self.vistas_flujo.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25,
            controls=[
                ft.Text("PAGO Y FINALIZACIÓN", size=28, weight="bold", color=COLOR_PRIMARIO),
                ft.Text(f"TOTAL: ${self.pedido_actual.total}", size=36, weight="bold", color=COLOR_EXITO),
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=20,
                    controls=[
                        self._boton_pago("EFECTIVO", ft.Icons.MONEY),
                        self._boton_pago("TARJETA", ft.Icons.CREDIT_CARD),
                    ]
                ),
                ft.Container(height=10),
                BotonAnimado("GUARDAR VENTA", on_click=self.finalizar_venta_total, bgcolor=COLOR_PRIMARIO, width=350, height=60),
                ft.TextButton("CORREGIR DATOS", on_click=lambda _: self.mostrar_formulario_cliente(), style=ft.ButtonStyle(color=ft.Colors.GREY_400))
            ]
        )
        self.update()

    def _boton_pago(self, metodo, icono):
        return ft.Container(
            content=ft.Column([ft.Icon(icono, size=40, color=COLOR_TEXTO), ft.Text(metodo, weight="bold")], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=150, height=120, bgcolor=COLOR_CONTRASTE, border_radius=15,
            on_click=lambda _, m=metodo: self.seleccionar_metodo_pago(m),
            animate_scale=ft.Animation(150, "bounceOut")
        )

    def seleccionar_metodo_pago(self, metodo):
        self.pedido_actual.metodo_pago = metodo
        self._mostrar_notificacion(f"Método: {metodo}", COLOR_NUEVO)

    async def finalizar_venta_total(self, e):
        """Cierre de ticket. Delegamos notificaciones al método privado de la clase."""
        if not self.pedido_actual.metodo_pago:
            # REDUNDANCIA ELIMINADA: Usamos la función interna de la clase
            self._mostrar_notificacion("POR FAVOR, SELECCIONE UN MÉTODO DE PAGO", COLOR_ERROR)
            return

        try:
            self.pedido_actual.estatus = ESTADO_PREPARANDO
            await self.db.guardar_pedido(self.pedido_actual)
            
            id_guardado = self.pedido_actual.id or 'OK'
            
            self.pedido_actual = Pedido() 
            self.preparar_interfaz_inicial()
            
            # REDUNDANCIA ELIMINADA: Usamos la función interna
            self._mostrar_notificacion(f"✅ ¡VENTA REGISTRADA! TICKET #{id_guardado}", COLOR_EXITO)
            
        except Exception as ex:
            # REDUNDANCIA ELIMINADA: Usamos la función interna
            self._mostrar_notificacion(f"ERROR CRÍTICO AL GUARDAR: {str(ex)}", COLOR_ERROR)