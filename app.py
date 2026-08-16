import streamlit as st
import datetime

# -----------------------------------------------------------------------------
# Configuración de la página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sistema de Ordenes",
    layout="wide"
)

# Estilos visuales personalizados (Modo Oscuro como en la imagen)
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #161b22 !important;
        border-color: #30363d !important;
        border-radius: 6px;
    }
    .stForm {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 24px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Estructura principal del formulario
# -----------------------------------------------------------------------------
st.title("Gestión de Órdenes")

with st.form(key="ordenes_form", clear_on_submit=False):

    # FILA 1: Número de Orden (Auto) | Tipo de Servicio
    col1, col2 = st.columns(2)
    with col1:
        numero_orden = st.text_input(
            "Número de Orden (Auto)", 
            value="0000001", 
            disabled=True
        )
    with col2:
        tipo_servicio = st.selectbox(
            "Tipo de Servicio", 
            ["Bordado", "Digitalización 3D", "Digitalización Plana", "Diseño", "Otro"]
        )

    # FILA 2: Nombre de la Orden / Trabajo (NUEVO CAMPO)
    nombre_orden = st.text_input(
        "Nombre de la Orden / Trabajo", 
        placeholder="Ej. Logo Pecho Gorra Flexfit / Bordado Camisa"
    )

    # FILA 3: Nombre del Cliente | Fecha Estimada de Entrega
    col3, col4 = st.columns(2)
    with col3:
        nombre_cliente = st.text_input(
            "Nombre del Cliente", 
            placeholder="Ingrese el nombre del cliente"
        )
    with col4:
        fecha_entrega = st.date_input(
            "Fecha Estimada de Entrega", 
            value=datetime.date(2026, 8, 16)
        )

    # FILA 4: Teléfono
    telefono = st.text_input(
        "Teléfono", 
        placeholder=""
    )

    # FILA 5: TOTAL ($) | ABONO / ANTICIPO ($)
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

    # Botón invisible/submit estándar del formulario
    submit_button = st.form_submit_button(label="Guardar Orden", use_container_width=True)

# -----------------------------------------------------------------------------
# Lógica al procesar el formulario
# -----------------------------------------------------------------------------
if submit_button:
    if not nombre_orden.strip():
        st.error("Por favor, ingrese el Nombre de la Orden.")
    elif not nombre_cliente.strip():
        st.error("Por favor, ingrese el Nombre del Cliente.")
    else:
        saldo_pendiente = total - abono
        st.success(f"¡Orden '{nombre_orden}' para {nombre_cliente} guardada exitosamente!")
        
        # Objeto listo para insertar a Supabase / Base de Datos
        datos_orden = {
            "numero_orden": numero_orden,
            "tipo_servicio": tipo_servicio,
            "nombre_orden": nombre_orden,
            "nombre_cliente": nombre_cliente,
            "fecha_entrega": str(fecha_entrega),
            "telefono": telefono,
            "total": total,
            "abono": abono,
            "saldo_pendiente": saldo_pendiente
        }
