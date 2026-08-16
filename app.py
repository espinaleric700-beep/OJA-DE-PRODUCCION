from datetime import datetime
import re
import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ==============================================================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Configuración de listas maestras
LISTA_ESTADOS = ["Pendiente", "Recepción", "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"]
TALLAS_DISPONIBLES = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL", "3XL"]

# Conexión Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estilos CSS
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    [data-testid="stSidebar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

def subir_a_supabase(file_bytes, file_name, bucket="disenos", carpeta="inventario"):
    path = f"{carpeta}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==============================================================================
# AUTENTICACIÓN
# ==============================================================================
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "rol": ""})

if not st.session_state["autenticado"]:
    st.markdown("#### 🔐 Acceso al Sistema")
    u, p = st.text_input("Usuario"), st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if u.lower() == "admin" and p == "2580Admin":
            st.session_state.update({"autenticado": True, "rol": "Administrador"})
            st.rerun()
    st.stop()

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================
st.title("🧵 Pixel Thread")
tabs = st.tabs(["📋 Órdenes", "➕ Nueva Orden", "📦 Almacén"])

# TAB 1: ÓRDENES
with tabs[0]:
    st.subheader("📋 Gestión de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        for o in ordenes:
            with st.container(border=True):
                st.markdown(f"**Orden #{o.get('numero_orden', 'N/A')}** - {o.get('nombre_cliente')}")
                st.info(f"Estado: {o.get('estado')}")
    except Exception:
        st.error("No se pudieron cargar las órdenes.")

# TAB 2: NUEVA ORDEN
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    with st.form("form_orden"):
        nombre = st.text_input("Nombre del Cliente")
        estado = st.selectbox("Estado inicial", LISTA_ESTADOS)
        tallas = st.multiselect("Tallas requeridas", TALLAS_DISPONIBLES)
        if st.form_submit_button("Crear Orden"):
            supabase.table("ordenes").insert({"nombre_cliente": nombre, "estado": estado, "tallas": tallas}).execute()
            st.success("Orden registrada.")
            st.rerun()

# TAB 3: ALMACÉN
with tabs[2]:
    st.subheader("📦 Inventario de Productos")
    
    with st.expander("➕ Agregar nuevo producto al stock"):
        with st.form("form_inventario"):
            prod_nombre = st.text_input("Nombre de la prenda")
            prod_color = st.text_input("Color")
            foto = st.file_uploader("Subir imagen de referencia", type=["png", "jpg"])
            
            if st.form_submit_button("Guardar en Inventario"):
                url_img = subir_a_supabase(foto.getvalue(), foto.name) if foto else ""
                try:
                    supabase.table("inventario").insert({
                        "nombre_prenda": prod_nombre,
                        "color": prod_color,
                        "imagen_url": url_img
                    }).execute()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error de base de datos: {e}")

    # Mostrar inventario
    try:
        inventario = supabase.table("inventario").select("*").execute().data
        for item in inventario:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if item.get("imagen_url"): st.image(item["imagen_url"], width=100)
                with c2:
                    st.markdown(f"**{item.get('nombre_prenda')}**")
                    st.write(f"🎨 Color: {item.get('color')}")
    except Exception:
        st.warning("La tabla de inventario no está configurada correctamente.")
