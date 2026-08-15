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

# Roles disponibles
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
            if rol_input == "Administrador" and clave_admin != "2580Admin":
                st.sidebar.error("Clave de Administrador incorrecta.")
            else:
                try:
                    res = supabase.table("usuarios").select("*").execute()
                    usuarios_db = res.data
                    
                    usuario_encontrado = None
                    limpio_input = usuario_input.strip().lower()
                    
                    for u in usuarios_db:
                        db_user = str(u.get("usuario") or "").strip().lower()
                        db_pass = str(u.get("password") or "")
                        
                        if db_user == limpio_input and db_pass == str(password_input):
                            usuario_encontrado = u
                            break

                    if usuario_encontrado:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = usuario_input
                        st.session_state["rol"] = usuario_encontrado.get("rol", rol_input)
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Usuario o contraseña incorrectos.")
                except Exception as e:
                    st.sidebar.error(f"Error al verificar credenciales: {e}")
    st.stop()

usuario = st.session_state["usuario"]
rol_seleccionado = st.session_state["rol"]

if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.session_state["usuario"] = ""
    st.session_state["rol"] = ""
    st.rerun()

ROLES_AUTORIZADOS_CREAR = ["Administrador", "Recepción", "Diseñador"]

mapa_roles = {
    "Recepción": ["Creada / Pendiente de Diseño", "Enviado a Transferencia Térmica"],
    "Diseñador": ["Creada / Pendiente de Diseño"],
    "Almacén": ["Enviado a Recepción"],
    "Producción - Bordados": ["En Producción"],
    "Producción - Impresión": ["En Producción"],
    "Transferencia Térmica": ["Enviado a Transferencia Térmica"]
}

# ==========================================
# FRAGMENTO PRINCIPAL
# ==========================================
@st.fragment(run_every=10)
def cargar_panel_principal():
    ordenes_db = supabase.table("ordenes").select("*").execute().data

    st.title("🧵 Pixel Thread - Gestión de Órdenes")
    busqueda = st.text_input("🔍 Buscador rápido (Número o Cliente)")

    if rol_seleccionado == "Administrador":
        tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
    else:
        tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

    with tab1:
        if ordenes_db:
            for o in ordenes_db:
                if o.get("estado_actual") in ["Cancelado", "Entregado"]: continue
                
                # Lógica de visibilidad por rol
                if rol_seleccionado != "Administrador":
                    estado = o.get("estado_actual")
                    area = o.get("area_produccion")
                    visible = False
                    if rol_seleccionado == "Recepción" and estado in ["Creada / Pendiente de Diseño", "Enviado a Transferencia Térmica"]: visible = True
                    elif rol_seleccionado == "Diseñador" and estado == "Creada / Pendiente de Diseño": visible = True
                    elif rol_seleccionado == "Almacén" and estado == "Enviado a Recepción": visible = True
                    elif rol_seleccionado == "Producción - Bordados" and estado == "En Producción" and area == "Bordados": visible = True
                    elif rol_seleccionado == "Producción - Impresión" and estado == "En Producción" and area == "Impresion": visible = True
                    elif rol_seleccionado == "Transferencia Térmica" and estado == "Enviado a Transferencia Térmica": visible = True
                    if not visible: continue

                if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and busqueda.lower() not in o.get("nombre_cliente", "").lower()): continue

                with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**"):
                    st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']}")
                    
                    # Lógica de cambio de estado simplificada
                    if st.button("🟢 Actualizar Estado", key=f"btn_{o['id']}"):
                        st.write("Selecciona nuevo estado...") # Placeholder para lógica real de botones de estado
                        st.rerun()

    with tab2:
        if rol_seleccionado in ROLES_AUTORIZADOS_CREAR:
            with st.form("form_nueva_orden", clear_on_submit=True):
                nombre_cliente = st.text_input("Cliente")
                nombre_orden = st.text_input("Nombre de la Orden")
                area = st.selectbox("Área", ["Bordados", "Impresion"])
                fecha = st.date_input("Fecha de Entrega Estimada")
                archivos = st.file_uploader("Diseños", accept_multiple_files=True)
                if st.form_submit_button("Crear Orden"):
                    num = f"ORD-{len(ordenes_db)+1:03d}"
                    urls = [subir_a_supabase(f.getvalue(), f.name) for f in archivos] if archivos else []
                    supabase.table("ordenes").insert({
                        "numero_orden": num, "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                        "area_produccion": area, "fecha_entrega": str(fecha),
                        "estado_actual": "Creada / Pendiente de Diseño", "archivo_diseno": ",".join(urls), "creado_por": usuario
                    }).execute()
                    st.success("✅ ¡Orden creada!")
                    st.rerun()

    if rol_seleccionado == "Administrador":
        with tab3:
            st.subheader("👥 Gestión de Usuarios")
            with st.expander("➕ Registrar Nuevo Usuario"):
                n_nombre = st.text_input("Nombre Completo")
                n_user = st.text_input("Nombre de Usuario")
                n_pass = st.text_input("Contraseña", type="password")
                n_rol = st.selectbox("Rol Asignado", roles_disponibles)
                
                if st.button("Guardar Usuario"):
                    try:
                        # Se guarda 'rol' como texto para evitar el error de integer
                        supabase.table("usuarios").insert({
                            "nombre": n_nombre, "usuario": n_user, "password": n_pass, "rol": n_rol
                        }).execute()
                        st.success("Usuario creado con éxito.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al registrar usuario: {e}")

            st.subheader("🛠️ Usuarios Existentes")
            usuarios = supabase.table("usuarios").select("*").execute().data
            for u in usuarios:
                with st.expander(f"👤 {u.get('nombre')} ({u.get('rol')})"):
                    # Aquí iría lógica de edición usando u.get('rol')
                    if st.button("🗑️ Eliminar", key=f"del_{u['id']}"):
                        supabase.table("usuarios").delete().eq("id", u['id']).execute()
                        st.rerun()

cargar_panel_principal()
