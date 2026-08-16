import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Pixel Thread - Gestión de Órdenes", layout="wide")

# --- SIMULEX / CONEXIÓN A SUPABASE (Ejemplo de estructura) ---
# Aquí irían tus funciones reales de Supabase y Google Drive
def obtener_archivos_de_orden(order_id):
    # Simulación: Consulta a Supabase los archivos de la orden
    if "db_archivos" not in st.session_state:
        st.session_state.db_archivos = {
            1: [
                {"id": "file_1", "name": "happy_birthday.pdf", "url": "#"}
            ]
        }
    return st.session_state.db_archivos.get(order_id, [])

def guardar_archivo_en_bd(order_id, archivo_subido):
    # TODO: Aquí subes el archivo a Google Drive / Supabase Storage 
    # y guardas el registro en tu base de datos relacional.
    nuevo_archivo = {
        "id": f"file_{datetime.now().timestamp()}",
        "name": archivo_subido.name,
        "url": "#"
    }
    if order_id not in st.session_state.db_archivos:
        st.session_state.db_archivos[order_id] = []
    st.session_state.db_archivos[order_id].append(nuevo_archivo)

def eliminar_archivo_de_bd(order_id, file_id):
    # TODO: Borrar de Google Drive y actualizar Supabase
    st.session_state.db_archivos[order_id] = [
        f for f in st.session_state.db_archivos.get(order_id, []) if f["id"] != file_id
    ]

# --- APLICACIÓN PRINCIPAL ---
st.title("🧵 Pixel Thread - Panel de Producción")

# Selección de Orden de ejemplo
order_id_actual = 1 

st.markdown(f"### 📋 Detalles de la Orden #{order_id_actual}")

# --- SECCIÓN DE ARCHIVOS ADJUNTOS (NUEVA IMPLEMENTACIÓN) ---
st.markdown("---")
st.markdown("### 📎 Archivos Adjuntos")

# Obtener archivos actuales de la orden
archivos_actuales = obtener_archivos_de_orden(order_id_actual)

# 1. Listar y Eliminar archivos existentes
if not archivos_actuales:
    st.info("No hay archivos adjuntos en esta orden.")
else:
    st.markdown("#### Archivos Actuales")
    for archivo in archivos_actuales:
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.markdown(f"📄 [{archivo['name']}]({archivo['url']})")
        with col2:
            if st.button("🗑️ Eliminar", key=f"del_{archivo['id']}"):
                eliminar_archivo_de_bd(order_id_actual, archivo['id'])
                st.toast(f"Archivo '{archivo['name']}' eliminado correctamente.", icon="🗑️")
                st.rerun()

st.markdown("---")

# 2. Subir Nuevos Archivos
st.markdown("#### 📤 Agregar Nuevos Archivos")
nuevos_archivos = st.file_uploader(
    "Selecciona archivos para añadir a esta orden", 
    accept_multiple_files=True,
    key=f"uploader_{order_id_actual}"
)

if nuevos_archivos:
    if st.button("💾 Guardar y Subir Archivos a la Orden", type="primary"):
        with st.spinner("Subiendo archivos y actualizando la orden..."):
            for archivo in nuevos_archivos:
                # Ejecuta la función de subida para cada archivo seleccionado
                guardar_archivo_en_bd(order_id_actual, archivo)
            
            st.success("¡Archivos subidos y orden actualizada con éxito!")
            st.rerun()

st.markdown("---")
