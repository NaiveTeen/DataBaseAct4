# DataBaseAct4
la base de datos para la act4 de la materia Diseño y Arquitectura de Software

# Sistema de Monitoreo Acuícola (SMA) — Base de Datos

Base de datos MySQL para el proyecto de **Acuática del Golfo S.A.**, empresa de piscicultura (tilapia y camarón) en Alvarado, Veracruz. Centraliza el monitoreo de temperatura, pH, oxígeno disuelto y salinidad de los estanques de cultivo.

## Contenido del repositorio

| Archivo | Qué hace |
|---|---|
| `01_esquema_y_datos.sql` | Crea la base de datos `sma_acuatico`, sus 5 tablas, y las carga con datos de ejemplo. |
| `02_privilegios.sql` | Crea 5 usuarios de MySQL con permisos diferenciados (lectura, escritura, edición, eliminación, admin). |

## Requisitos

- MySQL Server 8.0 o superior
- MySQL Workbench (u otro cliente como DBeaver / phpMyAdmin) para ejecutar los scripts

## Instalación

1. Abre MySQL Workbench y conéctate a tu servidor local.
2. Abre una nueva pestaña de consulta, pega el contenido de `01_esquema_y_datos.sql` y ejecútalo completo.
3. Abre otra pestaña, pega el contenido de `02_privilegios.sql` y ejecútalo completo.
4. Verifica que la base `sma_acuatico` aparezca en el panel de Schemas con sus 5 tablas.

> ⚠️ **Antes de usar en producción**, cambia las contraseñas de los usuarios definidas en `02_privilegios.sql` — están en texto plano como valores de ejemplo.

## Qué resuelve esta base de datos

Acuática del Golfo mide manualmente la temperatura, pH, oxígeno disuelto y salinidad de sus estanques, lo que retrasa detectar problemas (ej. baja oxigenación) y causa pérdidas económicas. Esta base de datos centraliza esos parámetros para que un dashboard pueda mostrarlos en tiempo real y generar alertas automáticas, en vez de depender de revisiones visuales manuales.

## Estructura de las tablas

### `estanques`
Catálogo de los estanques físicos de la granja.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT (PK) | Identificador único del estanque |
| `nombre` | VARCHAR(50) | Nombre del estanque (ej. "Estanque A1") |
| `tipo_cultivo` | ENUM | `'tilapia'` o `'camaron'` |
| `capacidad_m3` | DECIMAL | Volumen del estanque en metros cúbicos |
| `fecha_alta` | DATE | Fecha en que el estanque entró en operación |

### `sensores`
Qué sensor mide qué parámetro, en qué estanque. Cada estanque tiene 4 sensores (uno por parámetro).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT (PK) | Identificador único del sensor |
| `estanque_id` | INT (FK → `estanques.id`) | A qué estanque pertenece |
| `parametro` | ENUM | `'temperatura'`, `'ph'`, `'oxigeno_disuelto'` o `'salinidad'` |
| `modelo` | VARCHAR(50) | Modelo del sensor físico |
| `fecha_instalacion` | DATE | Fecha en que se instaló |

### `lecturas`
El histórico de mediciones — es la tabla más grande y la que alimenta las gráficas del dashboard.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT (PK) | Identificador único de la lectura |
| `sensor_id` | INT (FK → `sensores.id`) | Qué sensor generó el dato |
| `estanque_id` | INT (FK → `estanques.id`) | En qué estanque se tomó (redundante a propósito, para consultas más rápidas) |
| `valor` | DECIMAL(6,2) | El valor medido (unidad según el parámetro del sensor) |
| `fecha_hora` | DATETIME | Momento exacto de la medición |

### `alertas`
Se generan cuando un parámetro sale de su rango seguro.

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT (PK) | Identificador único de la alerta |
| `estanque_id` | INT (FK → `estanques.id`) | En qué estanque ocurrió |
| `parametro` | ENUM | Qué parámetro causó la alerta |
| `valor_detectado` | DECIMAL(6,2) | El valor que disparó la alerta |
| `nivel` | ENUM | `'bajo'`, `'medio'` o `'critico'` |
| `mensaje` | VARCHAR(150) | Descripción legible de la alerta |
| `fecha_hora` | DATETIME | Cuándo se generó |
| `atendida` | BOOLEAN | Si ya fue resuelta por un operario |

### `usuarios`
Personas que usarían la aplicación (no confundir con los usuarios de MySQL, ver más abajo).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | INT (PK) | Identificador único |
| `nombre` | VARCHAR(80) | Nombre completo |
| `email` | VARCHAR(100) | Correo (único) |
| `rol` | ENUM | `'operario'`, `'supervisor'` o `'administrador'` |
| `fecha_alta` | DATE | Fecha de registro |

### Cómo se relacionan las tablas

```
estanques (1) ───< (N) sensores (1) ───< (N) lecturas
    │
    └──────────────< (N) alertas
```

- Un **estanque** tiene varios **sensores** (uno por parámetro).
- Un **sensor** genera muchas **lecturas** a lo largo del tiempo.
- Un **estanque** puede generar varias **alertas**, sin pasar por un sensor específico (la alerta ya trae el parámetro y valor directamente).
- `usuarios` es independiente — no tiene llave foránea hacia las demás tablas todavía; se usaría más adelante si se agrega inicio de sesión o registro de "quién atendió qué alerta".

## Datos de ejemplo incluidos

| Tabla | Cantidad de registros | Detalle |
|---|---|---|
| `estanques` | 4 | 2 de tilapia, 2 de camarón |
| `sensores` | 16 | 4 por estanque (temperatura, pH, oxígeno disuelto, salinidad) |
| `lecturas` | 288 | 18 lecturas por sensor, simulando 3 días de monitoreo cada 4 horas |
| `alertas` | 5 | Ejemplos de niveles bajo, medio y crítico, en distintos estanques |
| `usuarios` | 4 | 2 operarios, 1 supervisor, 1 administrador |

### Rangos de valores simulados en `lecturas`

| Parámetro | Rango |
|---|---|
| Temperatura | 26 – 32 °C |
| pH | 6.5 – 8.0 |
| Oxígeno disuelto | 3 – 8 mg/L |
| Salinidad | 0 – 20 ppt |

## Usuarios de MySQL creados por `02_privilegios.sql`

| Usuario | Permisos | Uso previsto |
|---|---|---|
| `sma_lector` | `SELECT` | Dashboards y reportes de solo lectura |
| `sma_escritor` | `SELECT`, `INSERT` | Ingesta de lecturas desde los sensores |
| `sma_editor` | `SELECT`, `UPDATE` | Marcar alertas como atendidas, corregir registros |
| `sma_eliminador` | `SELECT`, `DELETE` | Depuración de históricos antiguos |
| `sma_admin` | Todos los privilegios | Administración total |

### ⚠️ No confundir con la tabla `usuarios`

La tabla `usuarios` (Juan Pérez, María López, etc.) son datos de la aplicación — personas que usarían el sistema, no tienen contraseña ni se conectan a MySQL. Los usuarios de esta tabla (`sma_lector`, `sma_admin`, etc.) son cuentas del propio servidor MySQL, con su propia contraseña definida en `IDENTIFIED BY`. Son dos capas distintas del sistema y no se relacionan entre sí.

## Cómo usar cada tipo de usuario

- **Para instalar y configurar la base de datos** (correr los scripts, revisar tablas en Workbench, hacer cambios de estructura): usa la cuenta **`root`** que configuraste al instalar MySQL. Es la única con permisos para crear bases de datos, tablas y otros usuarios.
- **Para conectar la base de datos a la página web / dashboard**: **no se debe usar `root`** en esa conexión, aunque sea más simple. La persona que construya el display debe usar la cuenta que corresponda a lo que la página realmente hace:
  - Si el dashboard **solo muestra estadísticas** (el caso más probable aquí) → usar **`sma_lector`** (solo `SELECT`, no puede alterar nada).
  - Si además la página va a **insertar** nuevas lecturas desde sensores → `sma_escritor`.
  - Si va a **marcar alertas como atendidas** o editar registros → `sma_editor`.

Usar una cuenta limitada en vez de `root` es buena práctica: si algo en el código de la página tiene un error o es comprometido, el daño posible queda limitado a lo que esa cuenta puede hacer (por ejemplo, `sma_lector` no podría borrar ni modificar nada aunque quisiera).

## Ejemplos de uso: agregar, editar y eliminar datos

Estos son ejemplos prácticos por si quieren probar que las gráficas cambian al modificar los datos. Cada bloque usa el usuario de MySQL correspondiente a esa acción.

### Agregar una nueva lectura (como `sma_escritor`)

Simula un sensor mandando un dato nuevo. Al insertarla, el promedio de esa gráfica cambia.

```sql
INSERT INTO lecturas (sensor_id, estanque_id, valor, fecha_hora)
VALUES (1, 1, 29.50, NOW());
```
- `sensor_id`: revisa la tabla `sensores` para saber cuál corresponde a qué parámetro (ej. sensor 1 = temperatura del Estanque A1).
- `estanque_id`: debe coincidir con el estanque de ese sensor.
- `valor`: el número que quieres simular.
- `NOW()` pone la fecha/hora actual automáticamente.

### Editar un registro (como `sma_editor`)

Ejemplo: marcar una alerta como atendida.

```sql
UPDATE alertas
SET atendida = TRUE
WHERE id = 2;
```

Ejemplo: corregir el valor de una lectura que se ingresó mal.

```sql
UPDATE lecturas
SET valor = 27.80
WHERE id = 15;
```

> ⚠️ Siempre usa un `WHERE` con el `id` exacto. Un `UPDATE` sin `WHERE` modifica **todas** las filas de la tabla.

### Eliminar un registro (como `sma_eliminador`)

Ejemplo: borrar una lectura de prueba que ya no se necesita.

```sql
DELETE FROM lecturas
WHERE id = 289;
```

Ejemplo: depurar lecturas más viejas de 30 días (limpieza de históricos).

```sql
DELETE FROM lecturas
WHERE fecha_hora < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

> ⚠️ Igual que con `UPDATE`, nunca corras un `DELETE` sin `WHERE` — borraría toda la tabla.

## Arquitectura de referencia

Esta base de datos corresponde a los siguientes componentes del backend del SMA:

- **MAD (Módulo de Adquisición de Datos)** → tablas `sensores` y `lecturas`, patrón **Observer** (la UI se suscribe al flujo de datos).
- **MPD (Módulo de Procesamiento)** → tabla `alertas`, patrón **Strategy** (la lógica de alerta es configurable).
- **DB (Base de Datos)** → histórico completo para gráficas y reportes, patrón **Modelo** (MVC/MVVM del frontend).
- **MAD (Módulo de Adquisición de Datos)** → tablas `sensores` y `lecturas`, patrón **Observer** (la UI se suscribe al flujo de datos).
- **MPD (Módulo de Procesamiento)** → tabla `alertas`, patrón **Strategy** (la lógica de alerta es configurable).
- **DB (Base de Datos)** → histórico completo para gráficas y reportes, patrón **Modelo** (MVC/MVVM del frontend).
