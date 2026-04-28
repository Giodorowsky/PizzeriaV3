import flet as ft  # Importamos la librería principal de la interfaz
from datos_negocio import COLOR_FONDO  # Importamos el color de fondo estándar de tus constantes
import traceback  # Herramienta para capturar y mostrar el rastro exacto de errores técnicos

class GestorNavegacion:  # Clase principal que administra el flujo de pantallas del sistema
    def __init__(self, page: ft.Page, db):  # El constructor recibe la página activa y la conexión a la base de datos
        self.page = page  # Guardamos la referencia de la página para manipular sus vistas
        self.db = db  # Guardamos la base de datos para heredarla a las pantallas que la requieran
        self.page.on_route_change = self.manejador_rutas  # Vinculamos el evento de cambio de ruta con nuestro manejador
        self.page.on_view_pop = self.manejador_pop  # Vinculamos el evento de retroceso (botón atrás) con nuestro manejador

    async def mostrar_login(self):  # Función asíncrona para iniciar la aplicación en la pantalla de PIN
        self.page.route = "/"  # Definimos la ruta raíz como punto de partida
        await self.manejador_rutas(None)  # Forzamos la construcción visual inicial para evitar pantallas negras

    async def procesar_login_exitoso(self, sesion):  # Se ejecuta cuando el cajero o dueño ingresa su PIN correcto
        self.page.session.store.set("usuario", sesion)  # Guardamos el usuario en el almacén de sesión actualizado (Flet 0.84.0)
        
        if sesion.rol == "DUEÑO":  # Si el usuario es el propietario...
            await self.page.push_route("/pos")  # Navegamos al POS (que ahora incluye estadísticas por deslizamiento)
        elif sesion.rol == "COCINA":  # Si el usuario es personal de cocina...
            await self.page.push_route("/cocina")  # Lo enviamos directamente al monitor de pedidos
        else:  # Para cajeras y el resto del personal...
            await self.page.push_route("/pos")  # Iniciamos el Punto de Venta estándar

    async def manejador_pop(self, e):  # Controla el comportamiento al retroceder en dispositivos Android
        if len(self.page.views) > 1:  # Verificamos que existan pantallas previas en el historial
            self.page.views.pop()  # Removemos la pantalla actual de la cima de la pila
            top_view = self.page.views[-1]  # Obtenemos la pantalla que quedó inmediatamente debajo
            await self.page.push_route(top_view.route)  # Navegamos de forma asíncrona a esa ruta anterior

    async def manejador_rutas(self, e):  # El motor que construye y dibuja cada vista según la navegación
        try:  # Bloque de seguridad para interceptar fallos de renderizado
            # Importaciones internas para evitar ciclos de dependencia entre archivos de vistas
            from views.login_view import LoginView
            from views.cocina_view import CocinaView
            from views.multi_view import MultiViewContainer
            from views.componentes.botones import BarraNavegacion

            self.page.views.clear()  # Limpiamos la lista de vistas para reconstruirla desde cero
            usuario = self.page.session.store.get("usuario")  # Recuperamos al usuario logueado del almacén de sesión

            # VALIDACIÓN DE SEGURIDAD: Si no estamos en login y no hay sesión, regresamos al PIN
            if self.page.route != "/" and usuario is None:
                await self.page.push_route("/")
                return

            # CONSTRUCCIÓN DE LA RUTA: LOGIN
            if self.page.route == "/":
                self.page.views.append(
                    ft.View(
                        route="/",  # Identificador de la pantalla inicial
                        controls=[LoginView(self.procesar_login_exitoso)],  # Cargamos la interfaz del teclado numérico
                        bgcolor= None ,  #COLOR_FONDO,  # Aplicamos el color oscuro de fondo
                        padding=0  # Sin márgenes para una experiencia inmersiva en celular
                    )
                )

            # CONSTRUCCIÓN DE LA RUTA: POS (Ahora con soporte para deslizamiento/swipe)
            elif self.page.route == "/pos":
                self.page.views.append(
                    ft.View(
                        route="/pos",
                        # La barra superior es dinámica y muestra íconos según el rol detectado
                        appbar=BarraNavegacion("PIZZERÍA", self.page),
                        # Cargamos el contenedor MultiView que permite el desplazamiento entre pantallas
                        controls=[MultiViewContainer(usuario, self.db)],
                        bgcolor=COLOR_FONDO,
                        padding=0
                    )
                )

            # CONSTRUCCIÓN DE LA RUTA: COCINA
            elif self.page.route == "/cocina":
                self.page.views.append(
                    ft.View(
                        route="/cocina",
                        appbar=BarraNavegacion("COCINA", self.page),
                        controls=[CocinaView(self.db)],  # Cargamos el monitor de tickets de cocina
                        bgcolor=COLOR_FONDO,
                        padding=0
                    )
                )

            # Actualizamos la página de forma asíncrona para una respuesta táctil fluida en Android
            self.page.update() 
            
        except Exception as ex:  # Captura de errores fatales en el flujo de vistas
            traza = traceback.format_exc()  # Generamos el reporte técnico del fallo
            self.page.views.append(  # Mostramos una pantalla de error visual para facilitar la corrección
                ft.View(
                    bgcolor=ft.Colors.BLACK,
                    padding=20,
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED, size=60),
                        ft.Text("ERROR DE VISTA (POO)", color=ft.Colors.RED, size=24, weight="bold"),
                        ft.Text(str(ex), color=ft.Colors.WHITE, size=18),
                        ft.Container(height=20),
                        ft.Text("Rastro para el desarrollador:", color=ft.Colors.GREY),
                        ft.Text(traza, color=ft.Colors.BLACK, size=12, selectable=True)
                    ]
                )
            )
            self.page.update()  # Forzamos la visualización del error