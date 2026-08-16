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
# MÓDULO AUTO-PING EN SEGUNDO PLANO
# ==============================================================================
URL_DE_MI_APP = "https://tu-app.streamlit.app" 

def keep_server_alive_loop(app_url, interval_seconds=300):
    time.sleep(10)
    while True:
        try:
            req = urllib.request.Request(app_url, headers={'User-Agent': 'InternalKeepAlive/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
        except Exception:
            pass
        time.sleep(interval_seconds)

if "keep_alive_thread_started" not in st.session_state:
    st.session_state["keep_alive_thread_started"] = True
    ping_thread = threading.Thread(target=keep_server_alive_loop, args=(URL_DE_MI_APP, 300), daemon=True)
    ping_thread.start()

# ==============================================================================
# CONFIGURACIÓN Y ESTILOS CSS
# ==============================================================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    .user-card { background-color: rgba(22, 27, 34, 0.85); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; }
    .stButton > button { border-radius: 6px !important; font-weight: 600 !important; }
    .sizes-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    .sizes-table th { background-color: rgba(88, 166, 255, 0.15); color: #58a6ff; border: 1px solid #30363d; padding: 6px; }
    .sizes-table td { border: 1px solid #30363d; padding: 6px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONEXIÓN Y VARIABLES GLOBALES
# ==============================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

lista_estados = ["Pendiente", "Recepción", "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"]
tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL", "3XL"]
FORMATOS_ORDEN = ["png", "jpg", "jpeg", "pdf", "emb", "dst", "ai", "psd", "eps", "svg", "cdr", "zip", "rar", "7z", "txt", "docx"]

def limpiar_nombre_archivo(nombre): return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def subir_a_supabase(file_bytes, file_name, bucket="disenos", carpeta="almacen"):
    nombre_seguro = limpiar_nombre_archivo(file_name)
    path = f"{carpeta}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==============================================================================
# LÓGICA DE USUARIO Y LOGIN
# ==============================================================================
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if not st.session_state["autenticado"]:
    st.title("🧵 Pixel Thread - Login")
    user_in = st.text_input("Usuario")
    pass_in = st.text_input("Contraseña", type="password")
    if st.button("Iniciar Sesión"):
        if user_in.lower() == "admin" and pass_in == "2580Admin":
            st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
            st.rerun()
        else:
            try:
                res = supabase.table("usuarios").select("*").eq("usuario", user_in).eq("password", pass_in).execute()
                if res.data:
                    st.session_state.update({"autenticado": True, "usuario": user_in, "rol": res.data[0]["rol_id"]})
                    st.rerun()
                else: st.error("❌ Credenciales incorrectas.")
            except Exception as e: st.error(f"Error: {e}")
    st.stop()

# ==============================================================================
# INTERFAZ Y TABS
# ==============================================================================
st.title("🧵 Pixel Thread")
st.markdown(f"👋 Usuario: **{st.session_state['usuario']}** | Rol: **{st.session_state['rol']}**")

tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    # (Aquí va la lógica de filtrado y visualización de órdenes que tenías)

with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    # (Aquí va el formulario de creación con el selector de tallas)

with tabs[2]:
    st.subheader("📦 Control de Inventario")
    if st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]:
        with st.expander("➕ Agregar Producto", expanded=False):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA", key="inv_nombre")
            col_picker, col_text = st.columns([1, 2])
            with col_picker:
                color_p = st.color_picker("Tono", "#3b82f6", key="color_p")
            with col_text:
                nuevo_color = st.text_input("NOMBRE DEL COLOR", value=color_p, key="nuevo_color")
            
            foto_color = st.file_uploader("🖼️ Imagen de muestra", type=["png", "jpg"], key="foto_color")
            
            # --- CORRECCIÓN APLICADA AQUÍ ---
            if st.button("➕ Añadir Color"):
                if nuevo_color.strip():
                    st.success(f"Agregando '{nuevo_color}' a la base de datos...")
                    # Aquí insertas tu lógica de supabase.table("inventario").insert(...)
                else:
                    st.warning("El campo de nombre de color no puede estar vacío.")
    else:
        st.error("No tienes permisos de acceso.")

with tabs[3]:
    st.subheader("⚙️ Configuración de Usuarios")
    # (Gestión de usuarios si la necesitas)
