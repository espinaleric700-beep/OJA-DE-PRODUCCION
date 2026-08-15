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
    # Usamos content-type genérico para admitir formatos de diseño pesados
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
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

rol_actual = str(st.session_state.get("rol", "")).strip()
rol_lower = rol_actual.lower()

# ------------------------------------------
# TAB 0: VER ÓRDENES Y CAMBIAR ESTADOS
# ------------------------------------------
with tabs[0]:
    st.subheader("📋 Listado y Control de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        if ordenes:
            estados_posibles = ["Pendiente", "En Proceso", "Completado", "Entregado"]
            
            for o in ordenes:
                area_orden = o.get('area', 'General')
                
                # Determinamos si el usuario actual tiene permiso para modificar esta orden específica
                # El Admin y Diseñador pueden ver y modificar todo. Los demás solo lo de su área respectiva.
                es_admin_o_disenador = rol_lower in ["administrador", "diseñador"]
                es_su_area = (rol_lower == "producción - bordados" and area_orden == "Bordado") or \
                             (rol_lower == "producción - impresión" and area_orden == "Impresión")
                
                puede_modificar = es_admin_o_disenador or es_su_area
                
                with st.expander(f"Orden #{o.get('id', 'N/A')} - Cliente: {o.get('cliente', 'General')} | Área: [{area_orden}] - Estado: {o.get('estado', 'Pendiente')}"):
                    st.write(f"**Área de Trabajo:** {area_orden}")
                    st.write(f"**Detalles:** {o.get('detalles', 'Sin detalles')}")
                    st.write(f"**Fecha de Creación:** {o.get('fecha', 'N/A')}")
                    
                    estado_actual = o.get('estado', 'Pendiente')
                    
                    if puede_modificar:
                        nuevo_estado = st.selectbox(
                            "Actualizar Estado de la Orden",
                            estados_posibles,
                            index=estados_posibles.index(estado_actual) if estado_actual in estados_posibles else 0,
                            key=f"estado_{o.get('id')}"
                        )
                        if st.button("Guardar Cambios de Estado", key=f"btn_{o.get('id')}"):
                            try:
                                supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", o.get("id")).execute()
                                st.success("✅ Estado actualizado correctamente.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al actualizar estado: {ex}")
                    else:
                        st.info(f"📌 Estado actual: **{estado_actual}** (Solo lectura para tu rol actual)")

                    imagenes = o.get('imagen_url')
                    if imagenes:
                        if isinstance(imagenes, str):
                            lista_archivos = [arch.strip() for arch in imagenes.split(",") if arch.strip()]
                        else:
                            lista_archivos = imagenes
                        
                        st.write("**Archivos y Diseños Adjuntos:**")
                        for idx, archivo_url in enumerate(lista_archivos):
                            nombre_archivo = archivo_url.split("/")[-1]
                            # Verificamos si es una imagen visualizable o un archivo descargable
                            if archivo_url.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                                st.image(archivo_url, width=200, caption=nombre_archivo)
                            else:
                                st.markdown(f"📥 [Descargar archivo {idx+1}: {nombre_archivo}]({archivo_url})")
        else:
            st.info("No hay órdenes registradas.")
    except Exception as e:
        st.error(f"Error al cargar las órdenes: {e}")

# ------------------------------------------
# TAB 1: NUEVA ORDEN (Restringido a Admin, Diseñador y Recepción)
# ------------------------------------------
with tabs[1]:
    roles_crear_orden = ["administrador", "diseñador", "recepción", "recepcion"]
    
    if rol_lower not in roles_crear_orden:
        st.error("⛔ Acceso denegado. Solo los roles de Administrador, Diseñador y Recepción pueden crear nuevas órdenes.")
    else:
        st.subheader("➕ Crear Nueva Orden")
        with st.form("form_nueva_orden", clear_on_submit=True):
            cliente = st.text_input("Nombre del Cliente")
            area = st.selectbox("Área de Producción", ["Bordado", "Impresión"])
            detalles = st.text_area("Detalles del Diseño / Requerimientos")
            
            # Extensiones solicitadas para archivos de diseño y formato general
            formatos_soportados = ["pdf", "png", "jpg", "jpeg", "ia", "psd", "cdr", "emb", "eps", "dst", "tbf", "svg"]
            archivos = st.file_uploader(
                "Subir Archivos (PDF, PNG, JPG, IA, PSD, CDR, EMB, EPS, DST, TBF, SVG)", 
                type=formatos_soportados, 
                accept_multiple_files=True
            )
            
            if st.form_submit_button("Guardar Orden"):
                try:
                    urls_archivos = []
                    if archivos:
                        for archivo in archivos:
                            url = subir_a_supabase(archivo.getvalue(), archivo.name)
                            urls_archivos.append(url)
                    
                    archivos_str = ",".join(urls_archivos)
                    
                    supabase.table("ordenes").insert({
                        "cliente": cliente,
                        "area": area,
                        "detalles": detalles,
                        "imagen_url": archivos_str,
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
    if rol_lower != "administrador":
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
                    rol_usu = u.get('rol_id') or u.get('rol') or 'Sin rol'
                    st.write(f"👤 **{u.get('nombre')}** | Usuario: `{u.get('usuario')}` | Rol: **{rol_usu}**")
            else:
                st.info("No hay usuarios registrados.")
        except Exception as e:
            st.error("No se pudieron cargar los usuarios.")
