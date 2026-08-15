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
    # Definir la ruta del archivo: carpeta/timestamp_nombreoriginal
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    
    # Subir el archivo a Supabase Storage
    supabase.storage.from_(bucket).upload(
        path=path,
        file=file_bytes,
        file_options={"content-type": "image/jpeg", "upsert": "true"}
    )
    
    # Obtener la URL pública
    url = supabase.storage.from_(bucket).get_public_url(path)
    return url

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
# PANEL PRINCIPAL
# ==========================================
st.title("🧵 Pixel Thread - Gestión de Órdenes")
busqueda = st.text_input("🔍 Buscador rápido (Número de orden, Cliente o Nombre de orden)")

tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])

with tab1:
    response = supabase.table("ordenes").select("*").execute()
    ordenes = response.data
    if ordenes:
        for o in ordenes:
            if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and 
                             busqueda.lower() not in o.get("nombre_cliente", "").lower()):
                continue

            with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']}")
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
                    st.rerun()

with tab2:
    with st.form("form_nueva_orden"):
        nombre_cliente = st.text_input("Nombre del Cliente")
        nombre_orden = st.text_input("Nombre de la Orden")
        area_produccion = st.selectbox("Área", ["Bordados", "Impresion"])
        archivos = st.file_uploader("Diseños", accept_multiple_files=True)
        if st.form_submit_button("Crear"):
            # Usar la nueva función de Supabase
            urls = [subir_a_supabase(f.getvalue(), f.name) for f in archivos]
            supabase.table("ordenes").insert({
                "numero_orden": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                "area_produccion": area_produccion, "estado_actual": "Creada / Pendiente de Diseño",
                "archivo_diseno": ",".join(urls), "creado_por": usuario
            }).execute()
            st.success("Orden creada con éxito")
            st.rerun()
