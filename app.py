from datetime import datetime
import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh
import json
import re

# ==========================================
# CONFIGURACIÓN Y ESTILO VISUAL (MODO OSCURO)
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

st_autorefresh(interval=10000, key="auto_refresh_ordenes")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    div.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #f9fafb; font-weight: 600; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; }
    p, label, span, div { color: #e5e7eb; }
    .stButton > button { border-radius: 6px; border: none; font-weight: 600; padding: 0.4rem 0.8rem; min-height: 2.2rem; }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

roles_disponibles = [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica"
]

lista_estados = [
    "Pendiente", "Recepción", "Producción - Bordados", "Producción - Impresión", 
    "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"
]

tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL"]

def limpiar_nombre_archivo(nombre): return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    nombre_seguro = limpiar_nombre_archivo(file_name)
    path = f"almacen/{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# Estado global inicial
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})
if "colores_inventario_avanzado" not in st.session_state:
    st.session_state["colores_inventario_avanzado"] = {}

# --- Autenticación ---
st.sidebar.title("🔐 Control de Acceso")
if not st.session_state["autenticado"]:
    usuario_input = st.sidebar.text_input("Usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Iniciar Sesión"):
        if usuario_input.strip().lower() == "admin" and password_input == "2580Admin":
            st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
            st.rerun()
        else:
            try:
                res = supabase.table("usuarios").select("*").execute()
                usuario_encontrado = next((u for u in res.data if u["usuario"].lower() == usuario_input.lower() and u["password"] == password_input), None)
                if usuario_encontrado:
                    st.session_state.update({"autenticado": True, "usuario": usuario_input, "rol": usuario_encontrado.get("rol_id", "")})
                    st.rerun()
                else: st.sidebar.error("❌ Usuario o contraseña incorrectos.")
            except Exception as e: st.sidebar.error(f"Error: {e}")
    st.stop()

st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

# --- Tabs ---
with tabs[0]:
    ordenes = supabase.table("ordenes").select("*").execute().data
    for o in ordenes:
        with st.expander(f"Orden #{o.get('numero_orden')} - {o.get('nombre_cliente')}"):
            st.write(f"Estado: {o.get('estado')}")

with tabs[2]:
    st.subheader("📦 Control de Inventario")
    
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Nuevo Producto con Colores, Tallas e Imagen por Color", expanded=False):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA", key="input_nombre_prenda_color_img")
            
            st.markdown("---")
            st.markdown("🎨 **Añadir Color, Tono y su Imagen Correspondiente**")
            
            col_picker, col_text = st.columns([1, 2])
            with col_picker:
                color_picker_val = st.color_picker("Tono", "#3b82f6", key="picker_color_hex_v2")
            with col_text:
                nuevo_color = st.text_input("NOMBRE O CÓDIGO DEL COLOR", value=color_picker_val, key="input_nuevo_color_nombre_v2")
            
            foto_color = st.file_uploader(f"🖼️ Subir Imagen para el color: `{nuevo_color}`", type=["png", "jpg", "jpeg"], key=f"uploader_img_{nuevo_color}")
            
            if st.button("➕ Añadir este Color al Producto"):
                if nuevo_color.strip():
                    c_clean = nuevo_color.strip()
                    if c_clean not in st.session_state["colores_inventario_avanzado"]:
                        st.session_state["colores_inventario_avanzado"][c_clean] = {
                            "tallas": {t: 0 for t in tallas_disponibles},
                            "imagen_file": foto_color,
                            "hex": color_picker_val if color_picker_val.startswith("#") else "#3b82f6"
                        }
                        st.success(f"Color '{c_clean}' agregado con éxito.")
                        st.rerun()
                    else:
                        st.warning("Este color ya está en la lista.")
                else:
                    st.error("Ingresa un nombre o código de color válido.")

            if st.session_state["colores_inventario_avanzado"]:
                st.markdown("#### 🔍 Configurar Existencias y Tallas por Color:")
                color_activo = st.selectbox("Selecciona color a configurar:", list(st.session_state["colores_inventario_avanzado"].keys()), key="select_color_activo_v2")
                
                if color_activo:
                    st.markdown(f"📏 **Tallas para `{color_activo}`**")
                    cols_grid = st.columns(3)
                    for idx, talla in enumerate(tallas_disponibles):
                        col_actual = cols_grid[idx % 3]
                        with col_actual:
                            val_actual = st.session_state["colores_inventario_avanzado"][color_activo]["tallas"].get(talla, 0)
                            nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=int(val_actual), key=f"cant_v2_{color_activo}_{talla}")
                            st.session_state["colores_inventario_avanzado"][color_activo]["tallas"][talla] = int(nueva_cant)
                            
                    if st.button("🗑️ Eliminar este color", key=f"del_col_v2_{color_activo}"):
                        del st.session_state["colores_inventario_avanzado"][color_activo]
                        st.rerun()

            st.markdown("---")
            if st.button("💾 Guardar Inventario Completo"):
                if not inv_nombre.strip():
                    st.error("⚠️ Debes ingresar el nombre del producto.")
                elif not st.session_state["colores_inventario_avanzado"]:
                    st.error("⚠️ Debes agregar al menos un color con sus tallas e imágenes.")
                else:
                    try:
                        data_a_guardar = {}
                        for col_key, col_data in st.session_state["colores_inventario_avanzado"].items():
                            img_file = col_data["imagen_file"]
                            img_url = ""
                            if img_file is not None:
                                img_url = subir_a_supabase(img_file.getvalue(), img_file.name)
                            
                            data_a_guardar[col_key] = {
                                "tallas": col_data["tallas"],
                                "imagen_url": img_url,
                                "hex": col_data.get("hex", "#3b82f6")
                            }
                        
                        supabase.table("almacen").insert({
                            "nombre_producto": inv_nombre,
                            "tallas_existencias": json.dumps(data_a_guardar),
                            "imagen_url": ""
                        }).execute()
                        
                        st.session_state["colores_inventario_avanzado"] = {}
                        st.success("✅ ¡Producto guardado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar producto: {e}")
        st.divider()

    try:
        inventario_db = supabase.table("almacen").select("*").execute().data
        if inventario_db:
            st.markdown("### 📋 Existencias Actuales en Almacén")
            for item in inventario_db:
                item_id = item.get("id")
                p_nombre = item.get("nombre_producto", "Sin nombre")
                p_tallas_str = item.get("tallas_existencias", "{}")

                # --- LECTURA SEGURA DE JSON PARA EVITAR CRASHES ---
                dict_colores = {}
                try:
                    if p_tallas_str:
                        dict_colores = json.loads(p_tallas_str)
                        if not isinstance(dict_colores, dict):
                            dict_colores = {}
                except Exception:
                    dict_colores = {}

                st.markdown(f"### 🏷️ {p_nombre}")
                
                if dict_colores:
                    lista_cols = list(dict_colores.keys())
                    key_activo = f"color_activo_{item_id}"
                    if key_activo not in st.session_state or st.session_state[key_activo] not in lista_cols:
                        st.session_state[key_activo] = lista_cols[0]
                    
                    st.markdown("Colores")
                    cols = st.columns(min(len(lista_cols), 6))
                    for idx, c_name in enumerate(lista_cols):
                        with cols[idx % len(cols)]:
                            if st.button(c_name, key=f"btn_{item_id}_{c_name}", use_container_width=True):
                                st.session_state[key_activo] = c_name
                                st.rerun()
                    
                    color_sel = st.session_state[key_activo]
                    data_color = dict_colores.get(color_sel, {})
                    
                    col_img, col_info = st.columns([1, 2])
                    with col_img:
                        if data_color.get("imagen_url"): 
                            st.image(data_color["imagen_url"], use_container_width=True)
                        else:
                            st.info("Sin imagen para este color")
                    with col_info:
                        st.markdown(f"**Existencias en color: `{color_sel}`**")
                        tallas_dict = data_color.get("tallas", {})
                        for talla in tallas_disponibles:
                            cant = tallas_dict.get(talla, 0)
                            st.write(f"- Talla {talla}: **{cant}**")
                else:
                    st.warning("⚠️ Este producto no tiene formato de colores estructurado o contiene datos inválidos.")

                if puede_modificar:
                    if st.button("🗑️ Eliminar Producto", key=f"del_prod_{item_id}"):
                        supabase.table("almacen").delete().eq("id", item_id).execute()
                        st.warning("⚠️ Producto eliminado.")
                        st.rerun()
                st.divider()
        else:
            st.info("No hay productos registrados en el almacén.")
    except Exception as e:
        st.error(f"Error al cargar el almacén: {e}")

with tabs[3]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Usuarios")
