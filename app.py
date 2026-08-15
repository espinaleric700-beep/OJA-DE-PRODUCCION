from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN Y CONEXIÓN
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "image/jpeg", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# Cargar roles desde la tabla 'rol'
try:
    res_roles = supabase.table("rol").select("*").execute()
    roles_db = res_roles.data if res_roles.data else []
    roles_disponibles = [r.get("id") or r.get("nombre_rol") for r in roles_db if (r.get("id") or r.get("nombre_rol"))]
    if not roles_disponibles:
        roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]
except:
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
    rol_input = st.sidebar.selectbox("Rol", roles_disponibles, key="input_rol")
    
    if rol_input == "Administrador":
        clave_admin = st.sidebar.text_input("Clave de Administrador", type="password", key="input_clave_admin")
    else:
        clave_admin = ""

    if st.sidebar.button("Iniciar Sesión"):
        if not usuario_input or not password_input:
            st.sidebar.warning("Por favor ingresa usuario y contraseña.")
        elif rol_input == "Administrador" and usuario_input.strip().lower() == "admin" and password_input == "2580Admin" and clave_admin == "2580Admin":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = "admin"
            st.session_state["rol"] = "Administrador"
            st.rerun()
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                for u in res.data:
                    if str(u.get("usuario") or "").lower() == usuario_input.strip().lower() and str(u.get("password") or "") == str(password_input):
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = usuario_input
                        st.session_state["rol"] = u.get("rol_id", rol_input)
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

if st.session_state["rol"] == "Administrador":
    tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
else:
    tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

with tab3: # Solo Admin
    st.subheader("👥 Registrar Nuevo Usuario")
    with st.form("form_reg_usuario"):
        n_nombre = st.text_input("Nombre Completo")
        n_user = st.text_input("Nombre de Usuario")
        n_pass = st.text_input("Contraseña", type="password")
        n_rol = st.selectbox("Rol Asignado", roles_disponibles)
        
        if st.form_submit_button("Guardar Usuario"):
            try:
                # Se usa 'rol_id' que es la columna existente en tu DB
                supabase.table("usuarios").insert({
                    "nombre": n_nombre, 
                    "usuario": n_user, 
                    "password": n_pass, 
                    "rol_id": n_rol
                }).execute()
                st.success("Usuario creado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar usuario: {e}")
