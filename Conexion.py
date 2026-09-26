from Backend import SMABackend

# Instanciar la clase backend
backend = SMABackend(
    host="localhost",
    user="sma_admin",
    password="Admin#2026",
    database="sma_acuatico",
    port=3306,
)

# 1. Para dar de alta un nuevo estanque (Pantalla 'Registro de Datos')
respuesta = backend.registrar_nuevo_estanque(
    nombre="Estanque B2", tipo_cultivo="tilapia", capacidad_m3=350.00
)
print(respuesta)

# 2. Para alimentar el Dashboard principal
estatus_tanques = backend.obtener_estatus_general()
print(estatus_tanques)

# 3. Para graficar el monitoreo de un tanque específico (ej. Tanque ID 1)
datos_graficas = backend.obtener_monitoreo_tanque(estanque_id=1)
print("Lectura actual pH:", datos_graficas["ph"]["actual"])

# 4. Para llenar los datos de la ventana Pop-Up con cálculo automático de fallas
info_popup = backend.obtener_info_popup_tanque(estanque_id=1)
print("Fallas activas:", info_popup["fallas"])