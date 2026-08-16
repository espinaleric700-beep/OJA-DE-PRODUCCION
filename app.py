import streamlit as st
import datetime

# -----------------------------------------------------------------------------
# Configuración de la página y Estilos CSS Personalizados (Modo Oscuro)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Ordenes - Pixel Thread",
    page_icon="🧵",
    layout="wide"
)

# Estilos CSS personalizados para replicar el diseño oscuro y bordes de la imagen
st.markdown("""
    <style>
    /* Estilo del contenedor principal */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Personalización de inputs y contenedores */
    div[data-baseweb="input"] {
        background-color: #1a1d24 !important;
        border-radius: 6px;
    }
    
    div[data-baseweb="select"] {
        background-color: #1a1d24 !important;
        border-radius: 6px;
    }

    /* Ajuste para tarjetas y formulario */
    .stForm {
        border: 1px solid #262730;
        border-radius: 10px;
        padding: 20px;
        background-color: #131720;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Función para obtener el siguiente número de orden (Auto-incremental)
# -----------------------------------------------------------------------------
def obtener_siguiente_numero_orden():
    # En producción, puedes consultar tu base de datos (Ej. Supabase)
    # SELECT count(*) FROM ordenes;
    return "0000001"

# -----------------------------------------------------------------------------
# Interfaz del Formulario
# -----------------------------------------------------------------------------
st.title("🧵 Registro de Nueva Orden")
st.markdown("Ingrese los detalles del trabajo y del cliente a continuación.")

with st.form(key="orden_form", clear_on_submit=False):
    
    # --- FILA 1: Número de Orden (Auto) y Tipo de Servicio ---
    col1, col2 = st.columns(2)
    with col1:
        numero_orden = st.text_input(
            "Número de Orden (Auto)", 
            value=obtener_siguiente_numero_orden(), 
            disabled=True
        )
    with col2:
        tipo_servicio = st.selectbox(
            "Tipo de Servicio", 
            [
                "Bordado", 
                "Digitalización para Bordado 3D (Puff)", 
                "Digitalización Plana", 
                "Diseño de Logo", 
                "Confección / Garment"
            ]
        )

    # --- FILA 2: Nombre / Título de la Orden ---
    nombre_orden = st.text_input(
        "Nombre de la Orden / Trabajo *", 
        placeholder="Ej. Logo Pecho Gorra Flexfit / Bordado Camisa Corporativa"
    )

    # --- FILA 3: Datos del Cliente y Fecha ---
    col3, col4 = st.columns(2)
    with col3:
        nombre_cliente = st.text_input(
            "Nombre del Cliente *", 
            placeholder="Ingrese el nombre del cliente o empresa"
        )
    with col4:
        fecha_entrega = st.date_input(
            "Fecha Estimada de Entrega", 
            value=datetime.date(2026, 8, 16)
        )

    # --- FILA 4: Teléfono de Contacto ---
    telefono = st.text_input(
        "Teléfono", 
        placeholder="Ej. +1 809-XXX-XXXX"
    )

    # --- FILA 5: Archivo adjunto (Opcional - Logo / Arte) ---
    archivo_logo = st.file_uploader(
        "Adjuntar Archivo de Logo / Diseño (Opcional)", 
        type=["png", "jpg", "jpeg", "pdf", "emb", "dst", "pxf", "glb"]
    )

    # --- FILA 6: Total y Abono ---
    col5, col6 = st.columns(2)
    with col5:
        total = st.number_input(
            "TOTAL ($)", 
            min_value=0.0, 
            value=0.00, 
            step=1.00, 
            format="%.2f"
        )
    with col6:
        abono = st.number_input(
            "ABONO / ANTICIPO ($)", 
            min_value=0.0, 
            value=0.00, 
            step=1.00, 
            format="%.2f"
        )

    # --- FILA 7: Cálculo del Saldo Pendiente ---
    saldo_pendiente = total - abono
    
    st.markdown("---")
    st.markdown(f"### **Saldo Pendiente:** `${saldo_pendiente:,.2f}`")

    # Botón de Guardar
    submit_button = st.form_submit_button(
        label="Guardar Orden", 
        use_container_width=True
    )

# -----------------------------------------------------------------------------
# Lógica al enviar el formulario
# -----------------------------------------------------------------------------
if submit_button:
    # Validaciones básicas de campos obligatorios
    if not nombre_orden.strip():
        st.error("⚠️ El campo 'Nombre de la Orden' es obligatorio.")
    elif not nombre_cliente.strip():
        st.error("⚠️ El campo 'Nombre del Cliente' es obligatorio.")
    else:
        # Estructura del objeto listo para enviar a Supabase o Google Drive
        orden_data = {
            "numero_orden": numero_orden,
            "tipo_servicio": tipo_servicio,
            "nombre_orden": nombre_orden,
            "nombre_cliente": nombre_cliente,
            "fecha_entrega": str(fecha_entrega),
            "telefono": telefono,
            "total": float(total),
            "abono": float(abono),
            "saldo_pendiente": float(saldo_pendiente),
            "estado": "Pendiente",
            "creado_el": str(datetime.datetime.now())
        }

        # Mensaje de éxito en la interfaz
        st.success(f"✅ ¡Orden **#{numero_orden} - {nombre_orden}** guardada con éxito para **{nombre_cliente}**!")
        
        # Muestra un resumen de los datos guardados
        st.json(orden_data)
        
        # AQUÍ VA TU CÓDIGO DE CONEXIÓN A BASE DE DATOS (Ejemplo Supabase / Google Drive):
        # try:
        #     response = supabase.table("ordenes").insert(orden_data).execute()
        #     if archivo_logo:
        #         # Lógica para subir el archivo a Google Drive o Supabase Storage
        #         pass
        # except Exception as e:
        #     st.error(f"Error al guardar en la base de datos: {e}")
