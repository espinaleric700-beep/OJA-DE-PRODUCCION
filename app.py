from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Asegúrate de tener configurado st.secrets["supabase"]
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Cargar roles desde la tabla 'rol'
try:
    res_roles = supabase.table("rol").select("*").execute()
    roles_db = res_roles.data if res_roles.data else []
    # Extraemos el valor de la columna 'id' que contiene los nombres de los roles
    roles_disponibles = [r.get("id") for r in roles_db if r.get("id")]
except Exception:
    roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]

# ==========================================
# GESTIÓN DE SESIÓN Y AUTENTICACIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

st.sidebar.title("🔐 Control de Acceso")

if not st.session_state["autenticado"]:
    usuario_input = st.sidebar.text_input("Usuario", key="input_usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password", key="input_password")
    
    if st.sidebar.button("Iniciar Sesión"):
        if not usuario_input or not password_input:
            st.sidebar.warning("Por favor ingresa usuario y contraseña.")
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                for u in res.data:
                    if str(u.get("usuario") or "").lower() == usuario_input.strip().lower() and str(u.get("password") or "") == str(password_input):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = usuario_input
                        # Usamos la columna 'rol' que es donde guardaremos el texto
                        st.session_state["rol"] = u.get("rol", "")
                        st.rerun()
                st.sidebar.error("❌ Usuario o contraseña incorrectos.")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Gestión")

tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])

with tabs[2]: # Pestaña de Configuración
    st.subheader("👥 Registrar Nuevo Usuario")
    with st.form("form_reg_usuario"):
        n_nombre = st.text_input("Nombre Completo")
        n_user = st.text_input("Nombre de Usuario")
        n_pass = st.text_input("Contraseña", type="password")
        n_rol = st.selectbox("Rol Asignado", roles_disponibles)
        
        if st.form_submit_button("Guardar Usuario"):
            try:
                # CORRECCIÓN: Insertamos en la columna 'rol' (tipo text) 
                # en lugar de 'rol_id' (que causaba error de tipo int4)
                supabase.table("usuarios").insert({
                    "nombre": n_nombre, 
                    "usuario": n_user, 
                    "password": n_pass, 
                    "rol": n_rol 
                }).execute()
                st.success("Usuario creado con éxito.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar usuario: {e}")
