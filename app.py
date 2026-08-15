from datetime import datetime
import streamlit as st
from supabase import create_client

# Inicializar Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FUNCIÓN DE SUBIDA A SUPABASE ---
def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "image/jpeg", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# --- CONFIGURACIÓN UI ---
st.set_page_config(page_title="Pixel Thread", layout="wide")

# --- LOGIN Y ROLES ---
st.sidebar.title("🔐 Control de Acceso")
usuario = st.sidebar.text_input("Usuario")
rol_seleccionado = st.sidebar.selectbox("Rol", [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"
])

if not usuario:
    st.warning("Ingresa usuario para continuar.")
    st.stop()

# --- LÓGICA DE ALERTAS POR ROL ---
ordenes_db = supabase.table("ordenes").select("*").execute().data
pendientes = []

# Mapeo de estados críticos por rol
mapa_roles = {
    "Recepción": ["Creada / Pendiente de Diseño", "Enviado a Transferencia Térmica"],
    "Diseñador": ["Creada / Pendiente de Diseño"],
    "Almacén": ["Enviado a Recepción"],
    "Producción - Bordados": ["En Producción"],
    "Producción - Impresión": ["En Producción"],
    "Transferencia Térmica": ["Enviado a Transferencia Térmica"]
}

if rol_seleccionado in mapa_roles:
    pendientes = [o for o in ordenes_db if o["estado_actual"] in mapa_roles[rol_seleccionado]]
    if pendientes:
        st.sidebar.error(f"⚠️ Tienes {len(pendientes)} ordenes pendientes en tu área.")

# --- PANEL PRINCIPAL ---
st.title("🧵 Pixel Thread - Gestión de Órdenes")
tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

with tab1:
    for o in ordenes_db:
        with st.expander(f"Orden: {o['numero_orden']} | Estado: {o['estado_actual']}"):
            st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']}")
            # (Aquí mantienes tu lógica de botones de estado del código anterior)

with tab2:
    with st.form("form_nueva_orden"):
        nombre_cliente = st.text_input("Nombre del Cliente")
        nombre_orden = st.text_input("Nombre de la Orden")
        area_produccion = st.selectbox("Área", ["Bordados", "Impresion"])
        archivos = st.file_uploader("Diseños", accept_multiple_files=True)
        
        if st.form_submit_button("Crear"):
            # Lógica para numeración 001, 002...
            total_ordenes = len(ordenes_db) + 1
            num_formateado = f"{total_ordenes:03d}" 
            
            urls = [subir_a_supabase(f.getvalue(), f.name) for f in archivos]
            supabase.table("ordenes").insert({
                "numero_orden": f"ORD-{num_formateado}",
                "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                "area_produccion": area_produccion, "estado_actual": "Creada / Pendiente de Diseño",
                "archivo_diseno": ",".join(urls), "creado_por": usuario
            }).execute()
            st.success(f"Orden ORD-{num_formateado} creada.")
            st.rerun()
