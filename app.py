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

# Lista por defecto para evitar "No options to select"
roles_por_defecto = [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"
]

roles_disponibles = roles_por_defecto
try:
    res_roles = supabase.table("rol").select("id").execute()
    if res_roles.data:
        roles_db = [r.get("id") for r in res_roles.data if r.get("id")]
        roles_disponibles = list(set(roles_por_defecto + roles_db))
except Exception:
    pass

# ==========================================
# GESTIÓN DE SESIÓN Y AUTENTICACIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""

st.sidebar.title("🔐 Control de Acceso")

if not st.session_state["autenticado"]:
    usuario_input = st.sidebar.text_input("Usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password")
    
    if st.sidebar.button("Iniciar Sesión"):
        if not usuario_input or not password_input:
            st.sidebar.warning("Por favor ingresa usuario y contraseña.")
        elif usuario_input.strip().lower() == "admin" and password_input == "2580Admin":
            st.session_state["autenticado"] = True
            st.session_state["usuario"] = "admin"
            st.session_state["rol"] = "Administrador"
            st.rerun()
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                usuario_encontrado = None
                for u in res.data:
                    if str(u.get("usuario") or "").lower() == usuario_input.strip().lower() and str(u.get("password") or "") == str(password_input):
                        usuario_encontrado = u
                        break
                
                if usuario_encontrado:
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = usuario_input
                    st.session_state["rol"] = usuario_encontrado.get("rol_id", "")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Usuario o contraseña incorrectos.")
            except Exception as e:
                st.sidebar.error(f"Error de conexión: {e}")
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.sidebar.info(f"👤 Conectado como: **{st.session_state['usuario']}**\n\n🛡️ Rol: **{st.session_state['rol']}**")

st.title("🧵 Pixel Thread - Gestión")

tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])

# ------------------------------------------
# TAB 0: VER ÓRDENES
# ------------------------------------------
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        if ordenes:
            for o in ordenes:
                with st.expander(f"Orden #{o.get('id', 'N/A')} - Cliente: {o.get('cliente', 'General')}"):
                    st.write(f"**Detalles:** {o.get('detalles', 'Sin detalles')}")
                    st.write(f"**Estado:** {o.get('estado', 'Pendiente')}")
                    if o.get('imagen_url'):
                        st.image(o.get('imagen_url'), width=250)
        else:
            st.info("No hay órdenes registradas.")
    except Exception as e:
        st.error(f"Error al cargar las órdenes: {e}")

# ------------------------------------------
# TAB 1: NUEVA ORDEN
# ------------------------------------------
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    with st.form("form_nueva_orden", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente")
        detalles = st.text_area("Detalles del Diseño / Bordado")
        archivo = st.file_uploader("Subir Imagen o Referencia", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("Guardar Orden"):
            try:
                imagen_url = ""
                if archivo is not None:
                    imagen_url = subir_a_supabase(archivo.getvalue(), archivo.name)
                
                supabase.table("ordenes").insert({
                    "cliente": cliente,
                    "detalles": detalles,
                    "imagen_url": imagen_url,
                    "estado": "Pendiente",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }).execute()
                st.success("✅ Orden creada con éxito.")
            except Exception as e:
                st.error(f"Error al guardar la orden: {e}")

# ------------------------------------------
# TAB 2: CONFIGURACIÓN / USUARIOS (SOLO ADMIN)
# ------------------------------------------
with tabs[2]:
    if str(st.session_state.get("rol")).strip().lower() != "administrador":
        st.error("⛔ Acceso denegado. Esta sección es exclusiva para el Panel de Administración.")
    else:
        st.subheader("👥 Registrar Nuevo Usuario")
        with st.form("form_reg_usuario", clear_on_submit=True):
            n_nombre = st.text_input("Nombre Completo")
            n_user = st.text_input("Nombre de Usuario")
            n_pass = st.text_input("Contraseña", type="password")
            n_rol = st.selectbox("Rol Asignado", roles_disponibles)
            
            if st.form_submit_button("Guardar Usuario"):
                try:
                    supabase.table("usuarios").insert({
                        "nombre": n_nombre, 
                        "usuario": n_user, 
                        "password": n_pass, 
                        "rol_id": n_rol
                    }).execute()
                    st.success("✅ Usuario creado con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar usuario: {e}")

        st.divider()
        st.subheader("🛠️ Usuarios Existentes")
        try:
            usuarios = supabase.table("usuarios").select("*").execute().data
            if usuarios:
                for u in usuarios:
                    rol_actual = u.get('rol_id') or u.get('rol') or 'Sin rol'
                    st.write(f"👤 **{u.get('nombre')}** | Usuario: `{u.get('usuario')}` | Rol: **{rol_actual}**")
            else:
                st.info("No hay usuarios registrados.")
        except Exception as e:
            st.error("No se pudieron cargar los usuarios.")
