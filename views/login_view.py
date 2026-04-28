import flet as ft
from modelos.usuario import Usuario 

class LoginView(ft.Container):
    def __init__(self, al_ingresar):
        super().__init__()
        self.al_ingresar = al_ingresar
        self.expand = True
        self.alignment = ft.Alignment.CENTER
        
        # Fondo completamente negro
        self.bgcolor = ft.Colors.BLACK 

        self.campo_nip = ft.TextField(
            label="PIN DE ACCESO",
            password=True,
            can_reveal_password=True,
            max_length=4,
            width=280,
            text_align=ft.TextAlign.CENTER,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=ft.Colors.ORANGE_700,
            focused_border_color=ft.Colors.ORANGE_ACCENT,
            color=ft.Colors.WHITE,
            on_submit=self.validar_acceso
        )

    def did_mount(self):
        config = self.page.session.store.get("config")
        nombre_negocio = config.obtener("nombre_negocio") if config else "MI NEGOCIO"
        
        # Eliminamos el ft.Card y dejamos los elementos flotando sobre el fondo negro
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            controls=[
                # AQUÍ VA TU LOGO: Asegúrate de tener "logo.png" en la carpeta assets
                ft.Image(src="mi_logitos.png", width=300, height=300, fit="contain"),
                ft.Container(height=10),
                
                ft.Text(nombre_negocio.upper(), size=32, weight="bold", color=ft.Colors.WHITE),
                ft.Text("Ingrese su PIN para continuar", color=ft.Colors.GREEN_700),
                ft.Container(height=30),
                
                self.campo_nip,
                ft.Container(height=20),
                
                ft.ElevatedButton(
                    "ENTRAR",
                    icon=ft.Icons.LOGIN_ROUNDED,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_700,
                        padding=20
                    ),
                    on_click=self.validar_acceso,
                    width=280
                )
            ]
        )
        self.update()

    # ... (Mantén tu función validar_acceso exactamente igual) ...

    async def validar_acceso(self, e):
        """Valida el PIN usando el Gestor de Configuración (Marca Blanca)."""
        nip = self.campo_nip.value
        config = self.page.session.store.get("config")
        
        if not config:
            self.campo_nip.error_text = "ERROR DE CONFIGURACIÓN"
            self.update()
            return

        seguridad = config.obtener("seguridad")
        
        # 1. Validar Dueño
        if nip == seguridad.get("pin_dueno"):
            sesion = Usuario(nombre="Administrador", rol="DUEÑO", esta_activo=True)
            await self.al_ingresar(sesion)
            
        # 2. Validar Cocina
        elif nip == seguridad.get("pin_cocina"):
            sesion = Usuario(nombre="Chef Principal", rol="COCINA", esta_activo=True)
            await self.al_ingresar(sesion)
            
        # 3. Validar Empleados (Busca en la lista de pines)
        elif nip in seguridad.get("pines_empleados", []):
            sesion = Usuario(nombre="Cajero", rol="CAJERA", esta_activo=True)
            await self.al_ingresar(sesion)
            
        else:
            # Feedback visual de error
            self.campo_nip.error_text = "PIN INCORRECTO"
            self.campo_nip.value = ""
            self.update()