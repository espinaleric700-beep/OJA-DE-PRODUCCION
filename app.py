from datetime import datetime
import streamlit as st
from supabase import create_client

# Configuración de página
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Estilo CSS profesional oscuro
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    .stButton > button { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; width: 100%; border-radius: 6px; font-weight: bold; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; padding: 20px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# Supabase Init
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- SESIÓN ---
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if not st.session_state["autenticado"]:
    st.sidebar.title("🔐 Acceso")
    u, p = st.sidebar.text_input("Usuario"), st.sidebar.text_input("Clave", type="password")
    if st.sidebar.button("Entrar"):
        res = supabase.table("usuarios").select("*").execute()
        usr = next((x for x in res.data if x["usuario"].lower() == u.lower() and x["password"] == p), None)
        if usr: 
            st.session_state.update({"autenticado": True, "usuario": u, "rol": usr.get("rol_id")})
            st.rerun()
    st.stop()

st.sidebar.button("🚪 Salir", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Panel de Control")
tabs = st.tabs(["📋 Órdenes", "➕ Nueva Orden", "⚙️ Usuarios"])

# --- TAB 0: ÓRDENES ---
with tabs[0]:
    ordenes = supabase.table("ordenes").select("*").execute().data
    for o in ordenes:
        c1, c2 = st.columns([4, 1])
        with c1:
            with st.expander(f"{o.get('numero_orden')} | {o.get('nombre_cliente')} | {o.get('estado')}"):
                st.write(f"**Piezas:** {o.get('piezas')} | **Área:** {o.get('area_produccion')}")
                st.write(f"**Detalles:** {o.get('nombre_orden')}")
                st.markdown(f"🕒 **Historial:**\n{o.get('historial')}")
        with c2:
            with st.form(f"f_{o.get('id')}"):
                nuevo = st.selectbox("Estado", ["Pendiente", "En Producción", "Listo", "Entregado"], index=0, label_visibility="collapsed")
                if st.form_submit_button("Actualizar"):
                    supabase.table("ordenes").update({"estado": nuevo}).eq("id", o.get("id")).execute()
                    st.rerun()

# --- TAB 1: NUEVA ORDEN (DATOS COMPLETOS) ---
with tabs[1]:
    with st.form("n_orden", clear_on_submit=True):
        col1, col2 = st.columns(2)
        cliente = col1.text_input("Nombre del Cliente")
        piezas = col2.number_input("Cantidad de Piezas", min_value=1)
        area = col1.selectbox("Área de Producción", ["Bordado", "Impresión"])
        detalles = col2.text_area("Detalles Técnicos (Front, Back, Medidas)")
        
        if st.form_submit_button("Crear Orden"):
            supabase.table("ordenes").insert({
                "numero_orden": f"ORD-{datetime.now().strftime('%Y%m%d%H%M')}",
                "nombre_cliente": cliente,
                "piezas": piezas,
                "area_produccion": area,
                "nombre_orden": detalles,
                "estado": "Pendiente",
                "historial": f"Creado por {st.session_state['usuario']} el {datetime.now().strftime('%Y-%m-%d')}"
            }).execute()
            st.success("✅ Orden registrada.")

# --- TAB 2: USUARIOS (DATOS COMPLETOS) ---
with tabs[2]:
    if st.session_state['rol'] == "Administrador":
        with st.form("nuevo_usuario"):
            nombre = st.text_input("Nombre Completo")
            user = st.text_input("Nombre de Usuario")
            pwd = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol", ["Administrador", "Diseñador", "Producción", "Recepción"])
            if st.form_submit_button("Registrar Usuario"):
                supabase.table("usuarios").insert({"nombre": nombre, "usuario": user, "password": pwd, "rol_id": rol}).execute()
                st.success("👤 Usuario creado.")
    else: st.warning("⛔ Acceso restringido.")
