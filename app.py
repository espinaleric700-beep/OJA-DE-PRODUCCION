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
# TAB 0: VER ÓRDENES Y FLUJO DE ESTADOS
# ------------------------------------------
with tabs[0]:
    st.subheader("📋 Listado y Control de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        if ordenes:
            for o in ordenes:
                area_orden = o.get('area', 'General')
                estado_actual = o.get('estado', 'Pendiente')
                
                with st.expander(f"Orden #{o.get('id', 'N/A')} - Cliente: {o.get('cliente', 'General')} | Área: [{area_orden}] - Estado: {estado_actual}"):
                    st.write(f"**Área de Trabajo:** {area_orden}")
                    st.write(f"**Detalles:** {o.get('detalles', 'Sin detalles')}")
                    st.write(f"**Fecha de Creación:** {o.get('fecha', 'N/A')}")
                    st.write(f"📌 **Estado Actual:** {estado_actual}")
                    
                    # Botones de cambio de estado basados en roles y flujo solicitado:
                    
                    # 1. Rol Diseñador: Puede enviar a recepción
                    if rol_lower == "diseñador" and estado_actual == "Pendiente":
                        if st.button("📤 Enviar a Recepción", key=f"btn_dis_{o.get('id')}"):
                            try:
                                supabase.table("ordenes").update({"estado": "Enviado a Recepción"}).eq("id", o.get("id")).execute()
                                st.success("✅ Orden enviada a recepción.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error: {ex}")

                    # 2. Roles de Producción y Almacén: Enviar a producción / marcar listo / completado
                    es_produccion_area = (rol_lower == "producción - bordados" and area_orden == "Bordado") or \
                                         (rol_lower == "producción - impresión" and area_orden == "Impresión")
                    es_almacen = rol_lower == "almacén" or rol_lower == "almacen"

                    if es_produccion_area or es_almacen:
                        if estado_actual in ["Enviado a Recepción", "Pendiente"]:
                            if st.button("🚀 Enviar a Producción", key=f"btn_prod_{o.get('id')}"):
                                try:
                                    supabase.table("ordenes").update({"estado": "En Producción"}).eq("id", o.get("id")).execute()
                                    st.success("✅ Orden enviada a producción.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                        if estado_actual == "En Producción":
                            if es_almacen and st.button("✔️ Marcar Listo (Almacén)", key=f"btn_alm_{o.get('id')}"):
                                try:
                                    # Si almacén da listo y producción ya completó o completamos ambos, regresa a recepción
                                    nuevo_est = "Listo en Almacén" if o.get('estado_produccion') != "Completado" else "Regresado a Recepción"
                                    supabase.table("ordenes").update({"estado_almacen": "Listo", "estado": nuevo_est}).eq("id", o.get("id")).execute()
                                    st.success("✅ Almacén actualizado.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                            if es_produccion_area and st.button("🏁 Marcar Completado (Producción)", key=f"btn_comp_{o.get('id')}"):
                                try:
                                    supabase.table("ordenes").update({"estado": "Regresado a Recepción"}).eq("id", o.get("id")).execute()
                                    st.success("✅ Producción completada. Orden devuelta a Recepción.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                    # 3. Rol Recepción o Administrador: Subir factura y entregar orden
                    es_recepcion = rol_lower in ["recepción", "recepcion"]
                    es_admin = rol_lower == "administrador"

                    if (es_recepcion or es_admin) and estado_actual in ["Regresado a Recepción", "Enviado a Recepción", "Pendiente"]:
                        st.markdown("---")
                        st.subheader("🧾 Gestión de Factura y Entrega")
                        factura_archivo = st.file_uploader("Subir Factura", type=["pdf", "png", "jpg", "jpeg"], key=f"fact_{o.get('id')}")
                        
                        if st.button("✅ Marcar Orden Entregada y Guardar Factura", key=f"btn_entregado_{o.get('id')}"):
                            try:
                                factura_url = o.get("factura_url", "")
                                if factura_archivo:
                                    factura_url = subir_a_supabase(factura_archivo.getvalue(), factura_archivo.name, bucket="disenos")
                                
                                supabase.table("ordenes").update({
                                    "estado": "Orden Entregada",
                                    "factura_url": factura_url
                                }).eq("id", o.get("id")).execute()
                                st.success("🎉 ¡Orden marcada como entregada con éxito!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al procesar la entrega: {ex}")

                    # Mostrar factura si existe
                    if o.get('factura_url'):
                        st.markdown(f"📄 [Ver Factura Adjunta]({o.get('factura_url')})")

                    # Visualización de archivos adjuntos iniciales
                    imagenes = o.get('imagen_url')
                    if imagenes:
                        if isinstance(imagenes, str):
                            lista_archivos = [arch.strip() for arch in imagenes.split(",") if arch.strip()]
                        else:
                            lista_archivos = imagenes
                        
                        st.write("**Archivos y Diseños Iniciales:**")
                        for idx, archivo_url in enumerate(lista_archivos):
                            nombre_archivo = archivo_url.split("/")[-1]
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
