from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN DE CONEXIONES
# ==========================================
st.set_page_config(
    page_title="Sistema de Órdenes - Pixel Thread",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "image/jpeg", "upsert": "true"}
    )
    return supabase.storage.from_(bucket).get_public_url(path)

# ==========================================
# AUTENTICACIÓN Y ROLES
# ==========================================
st.sidebar.title("🔐 Control de Acceso")
usuario = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")

roles_disponibles = [
    "Administrador", "Recepción", "Diseñador", "Almacén",
    "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica",
]
rol_seleccionado = st.sidebar.selectbox("Rol", roles_disponibles)

if rol_seleccionado == "Administrador":
    clave_admin = st.sidebar.text_input("Clave de Administrador", type="password")
    if clave_admin != "2580Admin":
        st.sidebar.error("Clave de Administrador incorrecta.")
        st.stop()

if not usuario:
    st.warning("Por favor, ingresa tu usuario para continuar.")
    st.stop()

# ==========================================
# MAPA DE ESTADOS PENDIENTES POR ROL
# ==========================================
mapa_roles = {
    "Recepción": ["Creada / Pendiente de Diseño", "Enviado a Transferencia Térmica"],
    "Diseñador": ["Creada / Pendiente de Diseño"],
    "Almacén": ["Enviado a Recepción"],
    "Producción - Bordados": ["En Producción"],
    "Producción - Impresión": ["En Producción"],
    "Transferencia Térmica": ["Enviado a Transferencia Térmica"]
}

# Obtener órdenes desde Supabase
ordenes_db = supabase.table("ordenes").select("*").execute().data

# Alerta en el sidebar
if rol_seleccionado in mapa_roles:
    pendientes_sidebar = [o for o in ordenes_db if o["estado_actual"] in mapa_roles[rol_seleccionado] and (rol_seleccionado != "Producción - Bordados" and rol_seleccionado != "Producción - Impresión" or o["area_produccion"] in rol_seleccionado)]
    if pendientes_sidebar:
        st.sidebar.error(f"⚠️ Tienes {len(pendientes_sidebar)} órdenes pendientes en tu área.")

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🧵 Pixel Thread - Gestión de Órdenes")
busqueda = st.text_input("🔍 Buscador rápido (Número de orden, Cliente o Nombre de orden)")

# Pestañas principales (incluyendo Configuración de Usuarios si es Admin)
if rol_seleccionado == "Administrador":
    tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
else:
    tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

with tab1:
    if ordenes_db:
        for o in ordenes_db:
            if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and 
                             busqueda.lower() not in o.get("nombre_cliente", "").lower()):
                continue

            # Verificar si esta orden está pendiente para el rol actual
            es_pendiente = False
            if rol_seleccionado == "Administrador":
                es_pendiente = True
            elif rol_seleccionado in mapa_roles and o["estado_actual"] in mapa_roles[rol_seleccionado]:
                if "Producción" in rol_seleccionado:
                    area_exacta = rol_seleccionado.split(" - ")[1]
                    if o["area_produccion"] == area_exacta:
                        es_pendiente = True
                else:
                    es_pendiente = True

            etiqueta_aviso = " 🔴 [PENDIENTE]" if es_pendiente else ""

            with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**{etiqueta_aviso}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']}")
                    st.write(f"**Creado por:** {o.get('creado_por', 'N/A')}")
                    if o.get("archivo_diseno"):
                        st.markdown(f"[🔗 Ver Archivo Diseño]({o['archivo_diseno']})")
                
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
                    # Opcional: Registrar historial de cambios si tienes la tabla historial_ordenes
                    try:
                        supabase.table("historial_ordenes").insert({
                            "orden_id": o["id"], "estado_anterior": estado, "estado_nuevo": nuevo_estado, "cambiado_por": usuario
                        }).execute()
                    except:
                        pass
                    st.rerun()

with tab2:
    with st.form("form_nueva_orden"):
        nombre_cliente = st.text_input("Nombre del Cliente")
        nombre_orden = st.text_input("Nombre de la Orden")
        area_produccion = st.selectbox("Área", ["Bordados", "Impresion"])
        archivos = st.file_uploader("Diseños", accept_multiple_files=True)
        
        if st.form_submit_button("Crear"):
            total_ordenes = len(ordenes_db) + 1
            num_formateado = f"{total_ordenes:03d}"
            
            urls = [subir_a_supabase(f.getvalue(), f.name) for f in archivos] if archivos else []
            supabase.table("ordenes").insert({
                "numero_orden": f"ORD-{num_formateado}",
                "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                "area_produccion": area_produccion, "estado_actual": "Creada / Pendiente de Diseño",
                "archivo_diseno": ",".join(urls), "creado_por": usuario
            }).execute()
            st.success(f"Orden ORD-{num_formateado} creada con éxito")
            st.rerun()

if rol_seleccionado == "Administrador":
    with tab3:
        st.subheader("👥 Gestión de Usuarios y Roles del Sistema")
        nuevo_usuario_input = st.text_input("Nuevo Usuario")
        rol_nuevo_input = st.selectbox("Rol Asignado", roles_disponibles, key="select_rol_nuevo")
        if st.button("Registrar Usuario"):
            if nuevo_usuario_input:
                try:
                    supabase.table("usuarios").insert({"usuario": nuevo_usuario_input, "rol": rol_nuevo_input}).execute()
                    st.success(f"Usuario {nuevo_usuario_input} registrado con éxito.")
                except Exception as e:
                    st.error(f"Error al registrar usuario (asegúrate de tener la tabla 'usuarios' creada): {e}")
            else:
                st.warning("Escribe un nombre de usuario.")
        
        st.markdown("---")
        st.subheader("📊 Historial de Órdenes Registradas")
        try:
            historial_db = supabase.table("historial_ordenes").select("*").execute().data
            if historial_db:
                st.dataframe(historial_db)
            else:
                st.info("No hay registros en el historial todavía.")
        except:
            st.info("La tabla 'historial_ordenes' no está configurada o está vacía en Supabase.")
