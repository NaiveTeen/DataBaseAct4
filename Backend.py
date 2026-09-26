from datetime import datetime
import mysql.connector
from mysql.connector import Error


class SMABackend:

    def __init__(
        self,
        host="localhost",
        user="sma_admin",
        password="Admin#2026",
        database="sma_acuatico",
        port=3306,
    ):
        """Inicializa la configuración de conexión a MySQL."""
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "port": port,
        }

    def _obtener_conexion(self):
        """Crea y retorna una conexión activa con el servidor MySQL."""
        return mysql.connector.connect(**self.config)

    # -------------------------------------------------------------------------
    # 1. PANTALLA BUSCADOR Y DASHBOARD DE ESTATUS
    # -------------------------------------------------------------------------

    def obtener_estatus_general(self):
        """Consulta todos los estanques y determina su estado global (OK o ALERTA).

        Un estanque está en 'ALERTA' si tiene alertas no atendidas.
        """
        conexion = self._obtener_conexion()
        cursor = conexion.cursor(dictionary=True)
        try:
            query = """
                SELECT 
                    e.id, 
                    e.nombre, 
                    e.tipo_cultivo,
                    COUNT(a.id) AS alertas_activas
                FROM estanques e
                LEFT JOIN alertas a 
                    ON e.id = a.estanque_id AND a.atendida = FALSE
                GROUP BY e.id, e.nombre, e.tipo_cultivo
                ORDER BY e.id ASC;
            """
            cursor.execute(query)
            estanques = cursor.fetchall()

            for estanque in estanques:
                estanque["estatus"] = (
                    "CRITICO" if estanque["alertas_activas"] > 0 else "OK"
                )

            return estanques
        finally:
            cursor.close()
            conexion.close()

    def existe_estanque(self, estanque_id):
        """Verifica si un estanque existe en la base de datos."""
        conexion = self._obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "SELECT id FROM estanques WHERE id = %s", (estanque_id,)
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()
            conexion.close()

    # -------------------------------------------------------------------------
    # 2. PANTALLA REGISTRO DE DATOS (DAR DE ALTA UN NUEVO ESTANQUE)
    # -------------------------------------------------------------------------

    def registrar_nuevo_estanque(
        self, nombre, tipo_cultivo, capacidad_m3, fecha_alta=None
    ):
        """Registra un nuevo estanque y genera automáticamente sus 4 sensores base.

        (Temperatura, pH, Oxígeno Disuelto, Salinidad).
        """
        if fecha_alta is None:
            fecha_alta = datetime.now().date()

        conexion = self._obtener_conexion()
        cursor = conexion.cursor()

        try:
            # Insertar el nuevo estanque
            query_estanque = """
                INSERT INTO estanques (nombre, tipo_cultivo, capacidad_m3, fecha_alta)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                query_estanque, (nombre, tipo_cultivo, capacidad_m3, fecha_alta)
            )
            nuevo_estanque_id = cursor.lastrowid

            # Crear automáticamente los 4 sensores obligatorios para este estanque
            parametros = [
                "temperatura",
                "ph",
                "oxigeno_disuelto",
                "salinidad",
            ]
            query_sensor = """
                INSERT INTO sensores (estanque_id, parametro, modelo, fecha_instalacion)
                VALUES (%s, %s, %s, %s)
            """

            for param in parametros:
                cursor.execute(
                    query_sensor,
                    (
                        nuevo_estanque_id,
                        param,
                        f"Sensor Standard {param.capitalize()}",
                        fecha_alta,
                    ),
                )

            conexion.commit()
            return {
                "exito": True,
                "estanque_id": nuevo_estanque_id,
                "mensaje": f"Estanque '{nombre}' registrado con éxito ID #{nuevo_estanque_id}.",
            }

        except Error as err:
            conexion.rollback()
            return {
                "exito": False,
                "mensaje": f"Error al registrar estanque: {err}",
            }
        finally:
            cursor.close()
            conexion.close()

    # -------------------------------------------------------------------------
    # 3. PANTALLA MONITOREO DE TANQUES (GRÁFICAS DE LÍNEA)
    # -------------------------------------------------------------------------

    def obtener_monitoreo_tanque(self, estanque_id, limite_lecturas=10):
        """Obtiene la última lectura de cada parámetro y los datos históricos

        necesarios para graficar las tendencias.
        """
        conexion = self._obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        try:
            query = """
                SELECT 
                    s.parametro,
                    l.valor,
                    l.fecha_hora
                FROM lecturas l
                INNER JOIN sensores s ON l.sensor_id = s.id
                WHERE l.estanque_id = %s
                ORDER BY l.fecha_hora DESC
            """
            cursor.execute(query, (estanque_id,))
            todas_lecturas = cursor.fetchall()

            # Estructurar lecturas organizadas por parámetro
            resultado = {
                "temperatura": {"actual": None, "historial": []},
                "ph": {"actual": None, "historial": []},
                "oxigeno_disuelto": {"actual": None, "historial": []},
                "salinidad": {"actual": None, "historial": []},
            }

            for reg in todas_lecturas:
                param = reg["parametro"]
                if len(resultado[param]["historial"]) < limite_lecturas:
                    resultado[param]["historial"].append(
                        {
                            "valor": float(reg["valor"]),
                            "fecha_hora": reg["fecha_hora"].strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                        }
                    )

            # Extraer el valor actual (más reciente) de cada parámetro
            for param in resultado:
                if resultado[param]["historial"]:
                    # Invertir historial para orden cronológico en la gráfica (de antiguo a nuevo)
                    resultado[param]["historial"].reverse()
                    resultado[param]["actual"] = resultado[param]["historial"][
                        -1
                    ]["valor"]

            return resultado

        finally:
            cursor.close()
            conexion.close()

    # -------------------------------------------------------------------------
    # 4. PANTALLA POP-UP: INFORMACIÓN Y CÁLCULO DE FALLAS (OPCIÓN B)
    # -------------------------------------------------------------------------

    def obtener_info_popup_tanque(self, estanque_id):
        """Recupera los datos del estanque y calcula dinámicamente las 'Fallas'

        consultando las alertas pendientes en la tabla `alertas`.
        """
        conexion = self._obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        try:
            # 1. Datos base del estanque
            cursor.execute(
                "SELECT * FROM estanques WHERE id = %s", (estanque_id,)
            )
            estanque = cursor.fetchone()

            if not estanque:
                return None

            # 2. Consultar fallas dinámicas desde la tabla `alertas` (no atendidas)
            query_alertas = """
                SELECT parametro, valor_detectado, nivel, mensaje, fecha_hora
                FROM alertas
                WHERE estanque_id = %s AND atendida = FALSE
                ORDER BY fecha_hora DESC
            """
            cursor.execute(query_alertas, (estanque_id,))
            alertas_pendientes = cursor.fetchall()

            # Formatear la lista de fallas
            fallas_list = []
            for a in alertas_pendientes:
                fallas_list.append(
                    f"[{a['nivel'].upper()}] {a['parametro'].replace('_', ' ').title()}: "
                    f"{a['mensaje']} (Valor: {a['valor_detectado']})"
                )

            # Estructurar respuesta para la UI
            popup_data = {
                "id": estanque["id"],
                "nombre": estanque["nombre"],
                "tipo_cultivo": estanque["tipo_cultivo"].capitalize(),
                "capacidad": f"{estanque['capacidad_m3']} m³",
                "fecha_alta": estanque["fecha_alta"].strftime("%d/%m/%Y"),
                "tiene_fallas": len(fallas_list) > 0,
                "fallas": (
                    fallas_list
                    if fallas_list
                    else ["Sin fallas detectadas actualmente."]
                ),
                "notas": (
                    "Estanque en condición de alerta. Requiere atención inmediata."
                    if fallas_list
                    else "Estanque operando dentro de los parámetros normales."
                ),
            }

            return popup_data

        finally:
            cursor.close()
            conexion.close()

    # -------------------------------------------------------------------------
    # 5. MÉTODOS AUXILIARES (INGESTA DE LECTURAS Y ALERTAS AUTOMÁTICAS)
    # -------------------------------------------------------------------------

    def registrar_lectura_manual(self, estanque_id, parametro, valor):
        """Registra una nueva lectura de un sensor e inserta automáticamente una alerta

        si el valor sale de los rangos de seguridad.
        """
        conexion = self._obtener_conexion()
        cursor = conexion.cursor(dictionary=True)

        try:
            # Buscar el sensor correspondiente del estanque
            cursor.execute(
                "SELECT id FROM sensores WHERE estanque_id = %s AND parametro = %s",
                (estanque_id, parametro),
            )
            sensor = cursor.fetchone()

            if not sensor:
                return {
                    "exito": False,
                    "mensaje": f"No existe sensor de {parametro} para el estanque {estanque_id}",
                }

            # Insertar la lectura
            now = datetime.now()
            cursor.execute(
                """
                INSERT INTO lecturas (sensor_id, estanque_id, valor, fecha_hora)
                VALUES (%s, %s, %s, %s)
            """,
                (sensor["id"], estanque_id, valor, now),
            )

            # Evaluar rangos de alerta
            alerta = self._evaluar_rango_parametro(
                parametro, float(valor)
            )
            if alerta:
                cursor.execute(
                    """
                    INSERT INTO alertas (estanque_id, parametro, valor_detectado, nivel, mensaje, fecha_hora, atendida)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                """,
                    (
                        estanque_id,
                        parametro,
                        valor,
                        alerta["nivel"],
                        alerta["mensaje"],
                        now,
                    ),
                )

            conexion.commit()
            return {
                "exito": True,
                "mensaje": "Lectura registrada correctamente.",
            }

        except Error as err:
            conexion.rollback()
            return {"exito": False, "mensaje": str(err)}
        finally:
            cursor.close()
            conexion.close()

    def _evaluar_rango_parametro(self, parametro, valor):
        """Rangos seguros para acuicultura."""
        rangos = {
            "temperatura": {"min": 26.0, "max": 32.0, "unidad": "°C"},
            "ph": {"min": 6.5, "max": 8.0, "unidad": "pH"},
            "oxigeno_disuelto": {"min": 3.0, "max": 8.0, "unidad": "mg/L"},
            "salinidad": {"min": 0.0, "max": 20.0, "unidad": "ppt"},
        }

        if parametro not in rangos:
            return None

        r = rangos[parametro]
        if valor < r["min"]:
            return {
                "nivel": "critico" if valor < (r["min"] * 0.8) else "bajo",
                "mensaje": f"Nivel {parametro} por debajo del límite seguro ({valor} {r['unidad']})",
            }
        elif valor > r["max"]:
            return {
                "nivel": "critico" if valor > (r["max"] * 1.2) else "medio",
                "mensaje": f"Nivel {parametro} por encima del límite seguro ({valor} {r['unidad']})",
            }
        return None