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
URL_DE_MI_APP = "https://tu-app.streamlit.app" 
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Inicialización Supabase segura con soporte para [supabase] en secrets o variables planas
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except Exception:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================
def obtener_siguiente_numero_orden():
    try:
        res = supabase.table("ordenes").select("numero_orden").execute()
        if res.data:
            numeros = [int(re.findall(r'\d+', str(row.get("numero_orden", "0")))[-1]) for row in res.data if re.findall(r'\d+', str(row.get("numero_orden", "0")))]
            return f"{(max(numeros) + 1):07d}" if numeros else "0000001"
    except: pass
    return "0000001"

def actualizar_talla_supabase(p_id, color, talla, nueva_cant, data_actual):
    try:
        data_actual[color]["tallas"][talla] = int(nueva_cant)
        supabase.table("almacen").update({"tallas_existencias": json.dumps(data_actual)}).eq("id", p_id).execute()
    except Exception as e:
        st.error(f"Error al actualizar: {e}")

# ==============================================================================
# CSS Y ESTILOS
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    div[data-testid="stNumberInput"] input { text-align: center; color: #3fb950 !important; font-weight: bold; }
    .user-card { background-color: rgba(22, 27, 34, 0.85); border: 1px solid #30363d; border-radius: 8px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESIÓN Y ESTADO
# ==============================================================================
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

# ==============================================================================
# LOGIN (Corregido para evitar errores por mayúsculas)
# ==============================================================================
if not st.session_state["autenticado"]:
    st.title("🔐 Acceso Pixel Thread")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        # Se usa .strip().lower() para aceptar 'Admin', 'ADMIN', 'admin', etc.
        if u.strip().lower() == "admin" and p == "2580Admin":
            st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# ==============================================================================
# TABS PRINCIPALES
# ==============================================================================
tabs = st.tabs(["📋 Órdenes", "➕ Nueva Orden", "📦 Almacén"])

with tabs[0]: # ÓRDENES
    st.subheader("📋 Listado de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        if ordenes:
            for o in ordenes:
                with st.container(border=True):
                    st.write(f"**Orden #{o.get('numero_orden')}** - {o.get('nombre_cliente')}")
        else:
            st.info("No hay órdenes registradas.")
    except Exception as e:
        st.error(f"Error al cargar órdenes: {e}")

with tabs[1]: # NUEVA ORDEN
    st.subheader("➕ Crear Orden")
    st.write(f"Siguiente número de orden sugerido: {obtener_siguiente_numero_orden()}")
    if st.button("Guardar Orden"): 
        st.success("Orden guardada.")

with tabs[2]: # ALMACÉN (EDICIÓN MANUAL)
    st.subheader("📦 Control de Inventario")
    try:
        productos = supabase.table("almacen").select("*").execute().data
        if productos:
            for prod in productos:
                p_id = prod.get("id")
                p_nombre = prod.get("nombre_producto")
                p_existencias_raw = prod.get("tallas_existencias", "{}")
                existencias = json.loads(p_existencias_raw)
                
                with st.container(border=True):
                    st.markdown(f"### 🏷️ {p_nombre}")
                    lista_colores = list(existencias.keys())
                    if lista_colores:
                        color_ver = st.selectbox("Color:", lista_colores, key=f"sel_{p_id}")
                        
                        dict_tallas = existencias.get(color_ver, {}).get("tallas", {})
                        st.markdown("✏️ *Cambia el número para guardar automáticamente:*")
                        
                        filas = [["2", "4", "6", "8", "10", "12", "14", "16"], ["S", "M", "WS", "WM", "L", "XL", "2XL", "3XL"]]
                        for fila in filas:
                            cols = st.columns(len(fila))
                            for idx, t in enumerate(fila):
                                with cols[idx]:
                                    val_actual = int(dict_tallas.get(t, 0))
                                    nuevo_val = st.number_input(f"{t}", min_value=0, value=val_actual, key=f"input_{p_id}_{color_ver}_{t}")
                                    
                                    if nuevo_val != val_actual:
                                        actualizar_talla_supabase(p_id, color_ver, t, nuevo_val, existencias)
                                        st.rerun() 
                    else:
                        st.warning("Este producto no tiene colores o tallas configuradas.")
        else:
            st.info("No hay productos en el almacén.")
    except Exception as e:
        st.error(f"Error en almacén: {e}")
