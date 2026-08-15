from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN Y ESTILO VISUAL (DARK MODE PRO)
# ==========================================
st.set_page_config(page_title="Pixel Thread - Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    div.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #f9fafb; font-weight: 600; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; }
    p, label, span, div { color: #e5e7eb; }
    .stButton > button { 
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); 
        color: white; border-radius: 6px; border: none; font-weight: 600; width: 100%;
    }
    .stButton > button:hover { background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%); }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
    </style>
""", unsafe_allow_html=True)

# Supabase Init
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==========================================
# GESTIÓN DE SESIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if not st.session_state["autenticado"]:
    st.sidebar.title("🔐 Acceso")
    u = st.sidebar.text_input("Usuario")
    p = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Entrar"):
        try:
            res = supabase.table("usuarios").select("*").execute()
            usr = next((x for x in res.data if x["usuario"].lower() == u.lower() and x["password"] == p), None)
            if usr:
                st.session_state.update({"autenticado": True, "usuario": u, "rol": usr.get("rol_id", "")})
                st.rerun()
            else: st.sidebar.error("❌ Credenciales inválidas.")
        except Exception as e: st.sidebar.error(str(e))
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread")
tabs = st.tabs(["📋 Órdenes", "➕ Nueva Orden", "⚙️ Usuarios"])

# TAB 0: ÓRDENES (Dashboard con selector lateral)
with tabs[0]:
    st.subheader("Control de Producción")
    ordenes = supabase.table("ordenes").select("*").execute().data
    lista_estados = ["Pendiente", "Enviado a Recepción", "En Producción", "Regresado a Recepción", "Orden Entregada"]
    
    if ordenes:
        for o in ordenes:
            estado_actual = o.get('estado') or 'Pendiente'
            color_map = {"Pendiente": "🟡", "Enviado a Recepción": "🔵", "En Producción": "🟠", "Regresado a Recepción": "🟣", "Orden Entregada": "🟢"}
            
            c1, c2 = st.columns([3, 1])
            with c1:
                with st.expander(f"{color_map.get(estado_actual, '⚪')} #{o.get('numero_orden')} - {o.get('nombre_cliente')}"):
                    st.write(f"**Área:** {o.get('area_produccion')}")
                    st.write(f"**Detalles:** {o.get('nombre_orden')}")
                    if o.get('factura_url'): st.markdown(f"[📄 Ver Archivo]({o.get('factura_url')})")
                    with st.expander("🕒 Historial"): st.markdown(o.get('historial') or "Sin registros.")
            
            with c2:
                with st.form(f"f_{o.get('id')}"):
                    nuevo = st.selectbox("Estado", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0, label_visibility="collapsed")
                    if st.form_submit_button("Actualizar"):
                        hist = f"• {nuevo} | {st.session_state['usuario']} | {datetime.now().strftime('%H:%M')}\n{o.get('historial', '')}"
                        supabase.table("ordenes").update({"estado": nuevo, "historial": hist}).eq("id", o.get("id")).execute()
                        st.rerun()

# TAB 1: NUEVA ORDEN
with tabs[1]:
    with st.form("n_orden", clear_on_submit=True):
        c, n, a = st.text_input("Cliente"), st.text_input("Detalles"), st.selectbox("Área", ["Bordados", "Impresion"])
        if st.form_submit_button("Guardar"):
            num = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            supabase.table("ordenes").insert({
                "numero_orden": num, "nombre_cliente": c, "nombre_orden": n, "area_produccion": a, "estado": "Pendiente",
                "historial": f"• Creada | {st.session_state['usuario']} | {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            }).execute()
            st.success("✅ Orden creada.")

# TAB 2: USUARIOS
with tabs[2]:
    if st.session_state['rol'] == "Administrador":
        # (Lógica de usuarios igual a la anterior)
        st.info("Sección de administración de usuarios activa.")
    else:
        st.warning("⛔ Solo administradores.")
