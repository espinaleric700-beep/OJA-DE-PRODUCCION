from datetime import datetime
import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh
import json
import re

# ==========================================
# CONFIGURACIÓN Y ESTILO VISUAL (MODO OSCURO)
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

st_autorefresh(interval=10000, key="auto_refresh_ordenes")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    div.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #f9fafb; font-weight: 600; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; }
    p, label, span, div { color: #e5e7eb; }
    .stButton > button { border-radius: 6px; border: none; font-weight: 600; padding: 0.4rem 0.8rem; min-height: 2.2rem; }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

roles_disponibles = [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica"
]

lista_estados = [
    "Pendiente", "Recepción", "Producción - Bordados", "Producción - Impresión", 
    "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"
]

tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL"]

def limpiar_nombre_archivo(nombre): return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    nombre_seguro = limpiar_nombre_archivo(file_name)
    path = f"almacen/{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# Estado global inicial
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})
if "colores_inventario_avanzado" not in st.session_state:
    st.session_state["colores_inventario_avanzado"] = {}

# --- Autenticación ---
st.sidebar.title("🔐 Control de Acceso")
if not st.session_state["autenticado"]:
    usuario_input = st.sidebar.text_input("Usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Iniciar Sesión"):
        if usuario_input.strip().lower() == "admin" and password_input == "2580Admin":
            st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
            st.rerun()
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                usuario_encontrado = next((u for u in res.data if u["usuario"].lower() == usuario_input.lower() and u["password"] == password_input), None)
                if usuario_encontrado:
                    st.session_state.update({"autenticado": True, "usuario": usuario_input, "rol": usuario_encontrado.get("rol_id", "")})
                    st.rerun()
                else: st.sidebar.error("❌ Usuario o contraseña incorrectos.")
            except Exception as e: st.sidebar.error(f"Error: {e}")
    st.stop()

st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

# --- Tabs ---
with tabs[0]:
    ordenes = supabase.table("ordenes").select("*").execute().data
    for o in ordenes:
        with st.expander(f"Orden #{o.get('numero_orden')} - {o.get('nombre_cliente')}"):
            st.write(f"Estado: {o.get('estado')}")

with tabs[2]:
    st.subheader("📦 Control de Inventario")
    inventario_db = supabase.table("almacen").select("*").execute().data
    
    for item in inventario_db:
        item_id = item.get("id")
        p_nombre = item.get("nombre_producto")
        dict_colores = json.loads(item.get("tallas_existencias", "{}"))
        
        st.markdown(f"### {p_nombre}")
        
        # --- CAMBIO IMPORTANTE: Botones Nativos ---
        lista_cols = list(dict_colores.keys())
        key_activo = f"color_activo_{item_id}"
        if key_activo not in st.session_state: st.session_state[key_activo] = lista_cols[0]
        
        # Creamos columnas para limitar el ancho de los botones
        cols = st.columns(len(lista_cols))
        for idx, c_name in enumerate(lista_cols):
            with cols[idx]:
                if st.button(c_name, key=f"btn_{item_id}_{c_name}", use_container_width=True):
                    st.session_state[key_activo] = c_name
                    st.rerun()
        
        # Mostrar contenido del color seleccionado
        color_sel = st.session_state[key_activo]
        data_color = dict_colores[color_sel]
        
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if data_color.get("imagen_url"): st.image(data_color["imagen_url"], use_container_width=True)
        with col_info:
            st.markdown(f"**Existencias en color: {color_sel}**")
            tallas = data_color.get("tallas", {})
            # Aquí iría tu lógica de botones +/- para las tallas...

with tabs[3]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Usuarios")
        # Lógica de usuarios...
