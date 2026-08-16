from datetime import datetime
import json
import re
import threading
import time
import urllib.request
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_js_eval import streamlit_js_eval
from supabase import create_client

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Conexión Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Estilos
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# Helper para subir archivos
def subir_a_supabase(file_bytes, file_name, bucket="disenos", carpeta="almacen"):
    path = f"{carpeta}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==============================================================================
# CONTROL DE ACCESO
# ==============================================================================
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if not st.session_state["autenticado"]:
    st.markdown("#### 🔐 Control de Acceso")
    u, p = st.text_input("Usuario"), st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if u.lower() == "admin" and p == "2580Admin":
            st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
            st.rerun()
    st.stop()

# ==============================================================================
# INTERFAZ PRINCIPAL
# ==============================================================================
st.title("🧵 Pixel Thread")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén"])

# TAB 1: ÓRDENES
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        for o in ordenes:
            with st.container(border=True):
                st.write(f"**Orden #{o.get('numero_orden')}** | Cliente: {o.get('nombre_cliente')}")
    except Exception as e:
        st.error("Error al cargar órdenes.")

# TAB 2: NUEVA ORDEN
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    with st.form("form_nueva_orden"):
        nombre = st.text_input("Nombre Cliente")
        if st.form_submit_button("Guardar Orden"):
            try:
                supabase.table("ordenes").insert({"nombre_cliente": nombre, "estado": "Pendiente"}).execute()
                st.success("Orden creada")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# TAB 3: ALMACÉN (CON PROTECCIÓN DE ERRORES)
with tabs[2]:
    st.subheader("📦 Control de Inventario")
    
    with st.expander("➕ Agregar Producto", expanded=False):
        with st.form("form_agregar_producto"):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA")
            nuevo_color = st.text_input("COLOR")
            foto_color = st.file_uploader("🖼️ Imagen", type=["png", "jpg"])
            
            if st.form_submit_button("💾 Guardar Producto"):
                url_foto = ""
                if foto_color:
                    url_foto = subir_a_supabase(foto_color.getvalue(), foto_color.name, bucket="disenos", carpeta="inventario")
                
                try:
                    supabase.table("inventario").insert({
                        "nombre_prenda": inv_nombre,
                        "color": nuevo_color,
                        "imagen_url": url_foto
                    }).execute()
                    st.success("Producto guardado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: La tabla 'inventario' no existe o no es accesible. {e}")

    # Visualización protegida
    st.markdown("---")
    try:
        res_inv = supabase.table("inventario").select("*").execute()
        if res_inv.data:
            for item in res_inv.data:
                with st.container(border=True):
                    st.markdown(f"#### {item.get('nombre_prenda')} | Color: {item.get('color')}")
        else:
            st.info("No hay productos registrados.")
    except Exception:
        st.warning("⚠️ La tabla 'inventario' no existe en Supabase. Por favor, créala para usar el Almacén.")
