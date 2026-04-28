import json
import flet as ft


def notificar_seguro(page, mensaje, color):
    """Lanzador de notificaciones a prueba de fallos."""
    try:
        snack = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE, weight="bold"), 
            bgcolor=color, 
            duration=3000
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()
    except Exception as e:
        print(f"Error al notificar: {e}")

#--------------------------------------------        
class GestorConfiguracion:
    """Clase para cargar la identidad del negocio desde un JSON externo."""
    def __init__(self, ruta="config.json"):
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                self.datos = json.load(f)
        except Exception:
            # Configuración de emergencia si el archivo no existe
            self.datos = {"nombre_negocio": "APP GENÉRICA", "tema": {"color_primario": "blue"}}

    def obtener(self, clave, subclave=None):
        """Busca un dato en el JSON. Ejemplo: obtener('tema', 'color_primario')"""
        if subclave:
            return self.datos.get(clave, {}).get(subclave)
        return self.datos.get(clave)