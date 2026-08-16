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
URL_DE_MI_APP = "https://tu-app.streamlit.app"  # <--- Reemplaza con tu URL real

def keep_server_alive_loop(app_url, interval_seconds=300):
    time.sleep(10)
    while True:
        try:
            req = urllib.request.Request(
                app_url, 
                headers={'User-Agent': 'InternalKeepAlive/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
        except Exception:
            pass
        time.sleep(interval_seconds)

if "keep_alive_thread_started" not in st.session_state:
    st.session_state["keep_alive_thread_started"] = True
    ping_thread = threading.Thread(
        target=keep_server_alive_loop, 
        args=(URL_DE_MI_APP, 300),
        daemon=True
    )
    ping_thread.start()

# ==============================================================================
# CONFIGURACIÓN Y ESTILOS CSS ADAPTATIVOS
# ==============================================================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

components.html(
    """
    <script>
    const meta = document.createElement('meta');
    meta.name = 'viewport';
    meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    document.getElementsByTagName('head')[0].appendChild(meta);

    function keepAlive() {
        fetch(window.location.href, {mode: 'no-cors'}).catch((err) => {});
    }
    setInterval(keepAlive, 120000);
    </script>
    """,
    height=0,
    width=0
)

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    .user-card { background-color: rgba(22, 27, 34, 0.85); border: 1px solid #30363d; border-radius: 8px; padding: 8px 12px; }
    .stButton > button { border-radius: 6px; background-color: #161b22; color: #ffffff; border: 1px solid #363b42; }
    .stButton > button:hover { border-color: #58a6ff; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background-color: rgba(22, 27, 34, 0.75) !important; border: 1px solid #30363d !important; border-left: 4px solid #58a6ff !important; border-radius: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# CONEXIÓN SUPABASE Y DATOS BASE
# ==============================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

lista_estados = ["Pendiente", "Recepción", "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"]
tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL", "3XL"]
FORMATOS_ORDEN = ["png", "jpg", "jpeg", "pdf", "emb", "dst", "ai", "psd", "eps", "svg", "cdr", "zip", "rar", "7z", "txt", "docx"]

def subir_a_supabase(file_bytes, file_name, bucket="disenos", carpeta="almacen"):
    path = f"{carpeta}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{re.sub(r'[^a-zA-Z0-9_.-]', '_', file_name)}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==============================================================================
# ESTADO E INICIO DE SESIÓN
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

# TAB 1: ÓRDENES (simplificado para brevedad)
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    ordenes = supabase.table("ordenes").select("*").execute().data
    for o in ordenes:
        with st.container(border=True):
            st.write(f"### Orden #{o.get('numero_orden')} - {o.get('nombre_cliente')}")

# TAB 2: NUEVA ORDEN
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    with st.form("form_nueva_orden"):
        nombre = st.text_input("Nombre Cliente")
        if st.form_submit_button("Guardar"):
            supabase.table("ordenes").insert({"nombre_cliente": nombre, "estado": "Pendiente"}).execute()
            st.success("Orden creada")

# TAB 3: ALMACÉN (Corregido)
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
                
                supabase.table("inventario").insert({
                    "nombre_prenda": inv_nombre,
                    "color": nuevo_color,
                    "imagen_url": url_foto
                }).execute()
                st.success("Guardado")
                st.rerun()

    # Visualización
    res_inv = supabase.table("inventario").select("*").execute()
    for item in res_inv.data:
        with st.container(border=True):
            st.markdown(f"#### {item.get('nombre_prenda')} | Color: {item.get('color')}")
