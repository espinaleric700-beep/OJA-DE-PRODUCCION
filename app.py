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
    
    roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]
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
                        db_user = str(u.get("usuario") or u.get("username") or u.get("name") or "").strip().lower()
                        db_pass = str(u.get("password") or u.get("pass") or "")
                        
                        if db_user == limpio_input and db_pass == str(password_input):
                            usuario_encontrado = u
                            break

                    if usuario_encontrado:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario"] = usuario_input
                        st.session_state["rol"] = rol_input
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
# FRAGMENTO CON AUTO-REFRESCO DE DATOS (Cada 10s)
# ==========================================
@st.fragment(run_every=10)
def cargar_panel_principal():
    ordenes_db = supabase.table("ordenes").select("*").execute().data

    if rol_seleccionado in mapa_roles:
        pendientes_sidebar = [o for o in ordenes_db if o["estado_actual"] in mapa_roles[rol_seleccionado] and (not "Producción" in rol_seleccionado or o["area_produccion"] in rol_seleccionado)]
        if pendientes_sidebar:
            st.sidebar.error(f"⚠️ Tienes {len(pendientes_sidebar)} órdenes pendientes.")

    st.title("🧵 Pixel Thread - Gestión de Órdenes")
    busqueda = st.text_input("🔍 Buscador rápido (Número o Cliente)")

    if rol_seleccionado == "Administrador":
        tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
    else:
        tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

    with tab1:
        if ordenes_db:
            for o in ordenes_db:
                if o["estado_actual"] == "Cancelado": 
                    continue
                
                if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and busqueda.lower() not in o.get("nombre_cliente", "").lower()):
                    continue

                with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**"):
                    col_info, col_acciones = st.columns([2, 1])
                    
                    with col_info:
                        st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']} | **Entrega:** {o.get('fecha_entrega', 'N/A')}")
                        st.write(f"**Creado por:** {o.get('creado_por', 'N/A')}")
                        if o.get("archivo_diseno"):
                            st.markdown(f"[🔗 Ver Archivo Diseño]({o['archivo_diseno']})")

                    with col_acciones:
                        if rol_seleccionado in ROLES_AUTORIZADOS_CREAR:
                            with st.popover("❌ Cancelar Orden"):
                                motivo = st.text_area("Motivo de cancelación", key=f"motivo_{o['id']}")
                                if st.button("Confirmar Cancelación", key=f"conf_cancel_{o['id']}"):
                                    if motivo:
                                        supabase.table("ordenes").update({"estado_actual": "Cancelado"}).eq("id", o["id"]).execute()
                                        supabase.table("historial_ordenes").insert({
                                            "orden_id": o["id"], "estado_anterior": o["estado_actual"], 
                                            "estado_nuevo": "CANCELADO", "motivo": motivo, "cambiado_por": usuario
                                        }).execute()
                                        st.rerun()
                                    else:
                                        st.warning("Escribe un motivo.")

                    estado = o["estado_actual"]
                    nuevo_estado = estado

                    if estado == "Creada / Pendiente de Diseño" and rol_seleccionado in ["Administrador", "Recepción", "Diseñador"]:
                        if st.button("🟢 Enviar a Recepción", key=f"btn_{o['id']}"): nuevo_estado = "Enviado a Recepción"
                    elif estado == "Enviado a Recepción" and rol_seleccionado in ["Administrador", "Recepción"]:
                        if st.button("🟢 Enviar a Almacén", key=f"btn_{o['id']}"): nuevo_estado = "Enviado a Almacén"
                    elif estado == "Enviado a Almacén" and rol_seleccionado in ["Administrador", "Almacén"]:
                        if st.button("🟢 Enviar a Producción", key=f"btn_{o['id']}"): nuevo_estado = "En Producción"
                    elif estado == "En Producción":
                        if o["area_produccion"] == "Bordados" and rol_seleccionado in ["Administrador", "Producción - Bordados"]:
                            if st.button("🟢 Completado", key=f"btn_{o['id']}"): nuevo_estado = "Completado"
                        elif o["area_produccion"] == "Impresion" and rol_seleccionado in ["Administrador", "Producción - Impresión"]:
                            if st.button("🟢 Enviar a Transferencia Térmica", key=f"btn_{o['id']}"): nuevo_estado = "Enviado a Transferencia Térmica"
                    elif estado == "Enviado a Transferencia Térmica" and rol_seleccionado in ["Administrador", "Transferencia Térmica"]:
                        if st.button("🟢 Enviar a Recepción", key=f"btn_{o['id']}"): nuevo_estado = "Enviado a Recepción"
                    elif estado in ["Completado", "Enviado a Recepción"] and rol_seleccionado in ["Administrador", "Recepción"]:
                        if st.button("🟢 Marcar como Entregado", key=f"btn_{o['id']}"): nuevo_estado = "Entregado"

                    if nuevo_estado != estado:
                        supabase.table("ordenes").update({"estado_actual": nuevo_estado}).eq("id", o["id"]).execute()
                        try:
                            supabase.table("historial_ordenes").insert({
                                "orden_id": o["id"], "estado_anterior": estado, "estado_nuevo": nuevo_estado, "cambiado_por": usuario
                            }).execute()
                        except:
                            pass
                        st.rerun()

    with tab2:
        if rol_seleccionado in ROLES_AUTORIZADOS_CREAR:
            with st.form("form_nueva_orden"):
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
                    st.success(f"Orden {num} creada con éxito")
                    st.rerun()
        else:
            st.error("⚠️ No tienes permisos para crear o modificar órdenes.")

    if rol_seleccionado == "Administrador":
        tab3_roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]
        with tab3:
            st.subheader("👥 Gestión de Usuarios")
            n_nombre = st.text_input("Nombre Completo (Obligatorio en BD)")
            n_user = st.text_input("Nombre de Usuario")
            n_pass = st.text_input("Contraseña", type="password")
            n_rol = st.selectbox("Rol", tab3_roles_disponibles, key="sel_rol_n")
            
            if st.button("Registrar Usuario"):
                if not n_nombre or not n_user or not n_pass:
                    st.warning("Por favor completa todos los campos.")
                else:
                    try:
                        # Incluimos 'nombre' y 'rol' que son requeridos por la estructura de la base de datos
                        supabase.table("usuarios").insert({
                            "nombre": n_nombre,
                            "usuario": n_user,
                            "password": n_pass,
                            "rol": n_rol
                        }).execute()
                        st.success("¡Usuario registrado con éxito en la base de datos!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo registrar automáticamente: {e}")
            
            st.markdown("---")
            st.subheader("📊 Historial de Movimientos y Cancelaciones")
            try:
                historial = supabase.table("historial_ordenes").select("*").execute().data
                st.dataframe(historial)
            except:
                st.info("No hay registros en el historial.")

cargar_panel_principal()
