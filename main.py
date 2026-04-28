import flet as ft
from database import DatabaseManager
from logic import GestorNavegacion
from views.componentes.ayuditas import notificar_seguro, GestorConfiguracion


async def main(page: ft.Page):
    config = GestorConfiguracion()
    page.session.store.set("config", config)
    db = DatabaseManager()
    await db.inicializar_db()
    page.title = config.obtener("nombre_negocio")
    #page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0 
    # Inicializamos el gestor que controlará las pantallas# Le pasamos 'page' para que él pueda dibujar en ella
    gestor = GestorNavegacion(page,db)
    await gestor.mostrar_login()

if __name__ == "__main__":
    ft.run(main)