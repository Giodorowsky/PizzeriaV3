import aiosqlite
import json
from datos_negocio import DB_COLUMNS, ESTADO_PREPARANDO

class DatabaseManager:
    def __init__(self, db_path="pizzeria.db"):
        self.db_path = db_path

    async def inicializar_db(self):
        """Prepara las tablas e inyecta la lógica de cierre de caja (CORTE)."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Tabla de Ventas (Con soporte para repartidores y cierres de turno)
            query_ventas = f'''
                CREATE TABLE IF NOT EXISTS ventas (
                    {DB_COLUMNS["ID"]} INTEGER PRIMARY KEY AUTOINCREMENT,
                    {DB_COLUMNS["FECHA"]} TEXT,
                    {DB_COLUMNS["CLIENTE"]} TEXT,
                    {DB_COLUMNS["TEL"]} TEXT,
                    {DB_COLUMNS["DIR"]} TEXT,
                    {DB_COLUMNS["DETALLE"]} TEXT,
                    {DB_COLUMNS["TOTAL"]} REAL,
                    {DB_COLUMNS["METODO"]} TEXT,
                    {DB_COLUMNS["SERVICIO"]} TEXT,
                    {DB_COLUMNS["ESTATUS"]} TEXT,
                    {DB_COLUMNS["REPARTIDOR"]} TEXT,
                    CORTE INTEGER DEFAULT 0 
                )
            '''
            await db.execute(query_ventas)

            # Verificación de integridad: Agrega columnas si la base de datos es antigua
            try: await db.execute("ALTER TABLE ventas ADD COLUMN CORTE INTEGER DEFAULT 0")
            except: pass 

            # 2. Tabla de Gastos
            await db.execute('''
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT,
                    monto REAL,
                    cajero TEXT,
                    fecha TEXT,
                    CORTE INTEGER DEFAULT 0
                )
            ''')
            try: await db.execute("ALTER TABLE gastos ADD COLUMN CORTE INTEGER DEFAULT 0")
            except: pass

            await db.commit()

    async def guardar_pedido(self, pedido):
        """Serializa el carrito de compras y guarda el ticket inicial."""
        detalle_texto = json.dumps([
            {"nombre": p.nombre, "sabores": p.sabores_elegidos} 
            for p in pedido.productos
        ])
        async with aiosqlite.connect(self.db_path) as db:
            columnas = DB_COLUMNS
            query = f'''
                INSERT INTO ventas (
                    {columnas["FECHA"]}, {columnas["CLIENTE"]}, {columnas["TEL"]}, 
                    {columnas["DIR"]}, {columnas["DETALLE"]}, {columnas["TOTAL"]}, 
                    {columnas["METODO"]}, {columnas["SERVICIO"]}, {columnas["ESTATUS"]},
                    {columnas["REPARTIDOR"]}
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            valores = (
                pedido.fecha.strftime("%Y-%m-%d %H:%M"), pedido.cliente_nombre,
                pedido.cliente_tel, pedido.cliente_dir, detalle_texto,
                pedido.total, pedido.metodo_pago, pedido.tipo_servicio,
                pedido.estatus, pedido.repartidor 
            )
            await db.execute(query, valores)
            await db.commit()

    async def obtener_pedidos_cocina(self):
        """Trae los pedidos activos para el monitor de preparación."""
        pedidos_cocina = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row 
            query = f"SELECT * FROM ventas WHERE {DB_COLUMNS['ESTATUS']} = '{ESTADO_PREPARANDO}' ORDER BY {DB_COLUMNS['ID']} ASC"
            async with db.execute(query) as cursor:
                async for fila in cursor:
                    pedidos_cocina.append({
                        "id": fila[DB_COLUMNS["ID"]],
                        "fecha": fila[DB_COLUMNS["FECHA"]],
                        "servicio": fila[DB_COLUMNS["SERVICIO"]],
                        "detalle": json.loads(fila[DB_COLUMNS["DETALLE"]]) 
                    })
        return pedidos_cocina
    
    async def actualizar_estatus_pedido(self, id_ticket, nuevo_estatus):
        """Cambia el estatus (PREPARANDO, LISTO, ENTREGADO)."""
        async with aiosqlite.connect(self.db_path) as db:
            query = f'UPDATE ventas SET {DB_COLUMNS["ESTATUS"]} = ? WHERE {DB_COLUMNS["ID"]} = ?'
            await db.execute(query, (nuevo_estatus, id_ticket))
            await db.commit()        

    async def actualizar_repartidor_pedido(self, id_ticket, repartidor):
        """Asigna el nombre del repartidor a una orden de domicilio."""
        async with aiosqlite.connect(self.db_path) as db:
            query = f'UPDATE ventas SET {DB_COLUMNS["REPARTIDOR"]} = ? WHERE {DB_COLUMNS["ID"]} = ?'
            await db.execute(query, (repartidor, id_ticket))
            await db.commit()

    async def guardar_gasto(self, gasto):
        """Registra una salida de efectivo de la caja."""
        async with aiosqlite.connect(self.db_path) as db:
            query = "INSERT INTO gastos (descripcion, monto, cajero, fecha) VALUES (?, ?, ?, ?)"
            valores = (gasto.descripcion, gasto.monto, gasto.cajero, gasto.fecha.strftime("%Y-%m-%d %H:%M"))
            await db.execute(query, valores)
            await db.commit()

    async def obtener_historial_pedidos(self):
        """Obtiene todos los pedidos del turno actual con detalles de contacto."""
        historial = []
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = f'SELECT * FROM ventas WHERE CORTE = 0 ORDER BY {DB_COLUMNS["ID"]} DESC LIMIT 50' 
            async with db.execute(query) as cursor:
                async for fila in cursor:
                    historial.append({
                        "id": fila[DB_COLUMNS["ID"]],
                        "fecha": fila[DB_COLUMNS["FECHA"]],
                        "cliente": fila[DB_COLUMNS["CLIENTE"]],
                        "total": fila[DB_COLUMNS["TOTAL"]],
                        "estatus": fila[DB_COLUMNS["ESTATUS"]],
                        "detalle": json.loads(fila[DB_COLUMNS["DETALLE"]]),
                        "tipo": fila[DB_COLUMNS["SERVICIO"]], 
                        "tel": fila[DB_COLUMNS["TEL"]],
                        "dir": fila[DB_COLUMNS["DIR"]],
                        "repartidor": fila[DB_COLUMNS["REPARTIDOR"]]
                    })
        return historial        

    async def obtener_resumen_dia(self):
        """Calcula el balance financiero del turno actual (Ventas vs Gastos)."""
        resumen = {
            "total": 0.0, "efectivo": 0.0, "tarjeta": 0.0, 
            "local": 0, "domicilio": 0, "gastos": 0.0, "neto_efectivo": 0.0
        }

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # 1. Sumatoria de Gastos operativos
            async with db.execute("SELECT SUM(monto) as tg FROM gastos WHERE CORTE = 0") as c:
                row = await c.fetchone()
                if row and row["tg"]: resumen["gastos"] = float(row["tg"])

            # 2. Análisis por Método de Pago
            query_dinero = f'''
                SELECT {DB_COLUMNS["METODO"]} as metodo, SUM({DB_COLUMNS["TOTAL"]}) as suma 
                FROM ventas WHERE CORTE = 0 GROUP BY {DB_COLUMNS["METODO"]}
            '''
            async with db.execute(query_dinero) as c:
                async for row in c:
                    suma = float(row["suma"] or 0)
                    if row["metodo"] == "EFECTIVO": resumen["efectivo"] += suma
                    elif row["metodo"] == "TARJETA": resumen["tarjeta"] += suma
                    resumen["total"] += suma

            # 3. Conteo de servicios
            query_pedidos = f'''
                SELECT {DB_COLUMNS["SERVICIO"]} as servicio, COUNT({DB_COLUMNS["ID"]}) as cantidad 
                FROM ventas WHERE CORTE = 0 GROUP BY {DB_COLUMNS["SERVICIO"]}
            '''
            async with db.execute(query_pedidos) as c:
                async for row in c:
                    cantidad = int(row["cantidad"] or 0)
                    if row["servicio"] == "LOCAL": resumen["local"] += cantidad
                    elif row["servicio"] == "DOMICILIO": resumen["domicilio"] += cantidad
            
            # Cálculo del dinero físico que el dueño debe recibir
            resumen["neto_efectivo"] = resumen["efectivo"] - resumen["gastos"]

        return resumen

    async def cerrar_dia_operativo(self):
        """Archiva las ventas y gastos actuales marcándolos como procesados (CORTE=1)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE ventas SET CORTE = 1 WHERE CORTE = 0")
            await db.execute("UPDATE gastos SET CORTE = 1 WHERE CORTE = 0")
            await db.commit()