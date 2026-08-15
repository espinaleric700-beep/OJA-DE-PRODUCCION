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

st_autorefresh(interval=15000, key="auto_refresh_ordenes")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    div.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #f9fafb; font-weight: 600; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; }
    p, label, span, div { color: #e5e7eb; }
    .stButton > button { border-radius: 4px; border: none; font-weight: 600; padding: 0.1rem 0.3rem; min-height: 1.5rem; font-size: 0.8rem; }
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

def obtener_siguiente_numero_orden():
    try:
        res = supabase.table("ordenes").select("numero_orden").execute()
        if res.data:
            numeros = []
            for row in res.data:
                val = row.get("numero_orden", "")
                nums_encontrados = re.findall(r'\d+', str(val))
                if nums_encontrados:
                    numeros.append(int(nums_encontrados[-1]))
            
            siguiente = max(numeros) + 1 if numeros else 1
            return f"{siguiente:07d}"
    except Exception:
        pass
    return "0000001"

def actualizar_estado_con_historial(o_id, estado_anterior, nuevo_estado, historial_actual, usuario_actual):
    if nuevo_estado == estado_anterior:
        return
    
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_registro = {
        "usuario": usuario_actual,
        "de": estado_anterior,
        "a": nuevo_estado,
        "fecha": ahora
    }
    
    lista_historial = []
    if historial_actual:
        if isinstance(historial_actual, str):
            try:
                lista_historial = json.loads(historial_actual)
            except Exception:
                lista_historial = []
        elif isinstance(historial_actual, list):
            lista_historial = historial_actual
            
    lista_historial.insert(0, nuevo_registro)
    
    supabase.table("ordenes").update({
        "estado": nuevo_estado,
        "historial": json.dumps(lista_historial)
    }).eq("id", o_id).execute()

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
    st.subheader("📋 Listado de Órdenes")
    
    filtro_estado = st.selectbox("Filtrar por Estado", ["Todos"] + lista_estados, key="filtro_estado_ordenes")
    
    try:
        query_ordenes = supabase.table("ordenes").select("*")
        if filtro_estado != "Todos":
            query_ordenes = query_ordenes.eq("estado", filtro_estado)
        
        ordenes = query_ordenes.execute().data
        
        if ordenes:
            for o in ordenes:
                o_id = o.get("id")
                numero_o = o.get('numero_orden', 'S/N')
                cliente_o = o.get('nombre_cliente', 'Sin cliente')
                estado_actual = o.get('estado', 'Pendiente')
                historial_db = o.get('historial', "[]")
                
                # Dividimos en 2 columnas: una para el selector rápido con botón y otra para el expander completo
                col_select, col_exp = st.columns([2.2, 3.8])
                
                with col_select:
                    sub_col_sel, sub_col_btn = st.columns([3, 1])
                    with sub_col_sel:
                        idx_actual = lista_estados.index(estado_actual) if estado_actual in lista_estados else 0
                        nuevo_estado_rapido = st.selectbox(
                            "Estado rápido", 
                            lista_estados, 
                            index=idx_actual, 
                            key=f"quick_est_{o_id}", 
                            label_visibility="collapsed"
                        )
                    with sub_col_btn:
                        if st.button("💾", key=f"btn_save_quick_{o_id}", help="Guardar nuevo estado"):
                            if nuevo_estado_rapido != estado_actual:
                                actualizar_estado_con_historial(
                                    o_id, estado_actual, nuevo_estado_rapido, 
                                    historial_db, st.session_state['usuario']
                                )
                                st.success("✅ Actualizado")
                                st.rerun()
                            else:
                                st.info("Es el mismo estado")

                with col_exp:
                    with st.expander(f"Orden #{numero_o} - {cliente_o} [Estado: {estado_actual}]"):
                        if st.session_state['rol'] in ["Administrador", "Recepción"]:
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                st.write(f"**Teléfono:** {o.get('telefono', 'N/D')}")
                                st.write(f"**Fecha de Entrega:** {o.get('fecha_entrega', 'N/D')}")
                                st.write(f"**Tipo de Servicio:** {o.get('tipo_servicio', 'N/D')}")
                            with col_info2:
                                st.write(f"**Total:** ${o.get('total', 0)}")
                                st.write(f"**Abono:** ${o.get('abono', 0)}")
                                st.write(f"**Restante:** ${o.get('restante', 0)}")
                            st.markdown("---")
                        
                        nuevo_estado_sel = st.selectbox("Cambiar Estado de la Orden", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0, key=f"select_est_{o_id}")
                        
                        if nuevo_estado_sel != estado_actual:
                            if st.button("💾 Actualizar Estado", key=f"btn_upd_est_{o_id}"):
                                actualizar_estado_con_historial(
                                    o_id, estado_actual, nuevo_estado_sel, 
                                    historial_db, st.session_state['usuario']
                                )
                                st.success("✅ ¡Estado actualizado y registrado en el historial!")
                                st.rerun()
                        
                        st.markdown("---")
                        st.markdown("📜 **Historial de Cambios de Estado:**")
                        try:
                            registros = json.loads(historial_db) if isinstance(historial_db, str) else historial_db
                            if registros:
                                for reg in registros:
                                    u_cambio = reg.get('usuario', 'Desconocido')
                                    de_est = reg.get('de', '-')
                                    a_est = reg.get('a', '-')
                                    f_cambio = reg.get('fecha', '-')
                                    st.caption(f"🕒 [{f_cambio}] 👤 **{u_cambio}** cambió el estado de *{de_est}* ➡️ *{a_est}*")
                            else:
                                st.caption("No hay cambios registrados todavía.")
                        except Exception:
                            st.caption("No se pudo cargar el historial.")
        else:
            st.info("No hay órdenes registradas con este filtro.")
    except Exception as e:
        st.error(f"Error al cargar las órdenes: {e}")

with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    
    numero_auto = obtener_siguiente_numero_orden()
    
    with st.form("form_crear_orden_completa"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.text_input("Número de Orden (Automático)", value=numero_auto, disabled=True)
            nombre_cliente = st.text_input("Nombre del Cliente")
            telefono_cliente = st.text_input("Teléfono del Cliente")
        with col_c2:
            tipo_servicio = st.selectbox("Tipo de Servicio", ["Bordado", "DTF", "Sublimación", "Mixto"])
            fecha_entrega = st.date_input("Fecha Estimada de Entrega")
            
        st.markdown("---")
        st.markdown("💰 **Información de Pago**")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            total_orden = st.number_input("Total ($)", min_value=0.0, step=100.0)
        with col_p2:
            abono_orden = st.number_input("Abono / Anticipo ($)", min_value=0.0, step=100.0)
        with col_p3:
            restante_calc = total_orden - abono_orden
            st.number_input("Restante ($)", value=max(0.0, restante_calc), disabled=True)
            
        observaciones = st.text_area("Observaciones o Detalles de la Orden")
        
        submit_nueva_orden = st.form_submit_button("💾 Guardar Orden Definitiva")
        if submit_nueva_orden:
            if nombre_cliente.strip():
                try:
                    historial_inicial = [{
                        "usuario": st.session_state['usuario'],
                        "de": "Inicio",
                        "a": "Pendiente",
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }]
                    
                    supabase.table("ordenes").insert({
                        "numero_orden": numero_auto,
                        "nombre_cliente": nombre_cliente,
                        "telefono": telefono_cliente,
                        "tipo_servicio": tipo_servicio,
                        "fecha_entrega": str(fecha_entrega),
                        "total": total_orden,
                        "abono": abono_orden,
                        "restante": max(0.0, restante_calc),
                        "observaciones": observaciones,
                        "estado": "Pendiente",
                        "historial": json.dumps(historial_inicial)
                    }).execute()
                    st.success(f"✅ ¡Orden #{numero_auto} creada y guardada correctamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar la orden: {e}")
            else:
                st.warning("⚠️ Debes ingresar el nombre del cliente.")

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

                dict_colores = {}
                try:
                    if p_tallas_str:
                        temp_data = json.loads(p_tallas_str)
                        if isinstance(temp_data, dict):
                            es_estructura_vieja = any(t in temp_data for t in tallas_disponibles)
                            if es_estructura_vieja:
                                dict_colores = {
                                    "Único": {
                                        "tallas": {t: int(temp_data.get(t, 0)) for t in tallas_disponibles},
                                        "imagen_url": item.get("imagen_url", ""),
                                        "hex": "#3b82f6"
                                    }
                                }
                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                            else:
                                dict_colores = temp_data
                except Exception:
                    dict_colores = {}

                st.markdown(f"### 🏷️ {p_nombre}")
                
                if dict_colores:
                    lista_cols = list(dict_colores.keys())
                    key_activo = f"color_activo_prod_{item_id}"
                    
                    if key_activo not in st.session_state or st.session_state[key_activo] not in lista_cols:
                        st.session_state[key_activo] = lista_cols[0]
                    
                    st.markdown("Colores")
                    cols_colores = st.columns(min(len(lista_cols), 4))
                    for idx, c_name in enumerate(lista_cols):
                        with cols_colores[idx % len(cols_colores)]:
                            if st.button(c_name, key=f"btn_color_item_{item_id}_{c_name}", use_container_width=True):
                                st.session_state[key_activo] = c_name
                                st.rerun()
                    
                    color_sel = st.session_state[key_activo]
                    data_color = dict_colores.get(color_sel, {})
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        if data_color.get("imagen_url"): 
                            st.image(data_color["imagen_url"], use_container_width=True)
                        else:
                            st.info("Sin imagen para este color")
                            
                    with col_info:
                        st.markdown(f"**Existencias para el color: `{color_sel}`**")
                        tallas_del_color = data_color.get("tallas", {})
                        
                        columna_1 = ["2", "4", "6", "8", "10"]
                        columna_2 = ["12", "14", "16", "S", "M"]
                        columna_3 = ["WS", "WM", "L", "XL", "2XL"]
                        
                        grid_cols = st.columns(3)
                        grupos_tallas = [columna_1, columna_2, columna_3]
                        
                        for col_idx, grupo in enumerate(grupos_tallas):
                            with grid_cols[col_idx]:
                                for talla in grupo:
                                    cantidad = int(tallas_del_color.get(talla, 0))
                                    
                                    if puede_modificar:
                                        sub1, sub2 = st.columns([1.2, 2.0])
                                        with sub1:
                                            st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='font-size: 0.85em; font-weight: bold; color: #4ade80;'>{talla}</span></div>", unsafe_allow_html=True)
                                        with sub2:
                                            nueva_cant = st.number_input(
                                                f"Talla {talla}", 
                                                min_value=0, 
                                                step=1, 
                                                value=cantidad, 
                                                key=f"num_{item_id}_{color_sel}_{talla}", 
                                                label_visibility="collapsed"
                                            )
                                            if nueva_cant != cantidad:
                                                dict_colores[color_sel]["tallas"][talla] = int(nueva_cant)
                                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                                st.rerun()
                                    else:
                                        st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='color: #4ade80;'>{talla}</span>: <b>{cantidad:02d}</b></div>", unsafe_allow_html=True)
                                    
                                    st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Este producto no tiene formato de colores estructurado o contiene datos inválidos.")

                if puede_modificar:
                    with st.expander(f"🛠️ Gestionar Colores e Imagen de: {p_nombre}"):
                        st.markdown("#### 🖼️ Cambiar o Subir Imagen para el Color Actual (`" + color_sel + "`)")
                        nueva_img_file = st.file_uploader(f"Nueva imagen para `{color_sel}`", type=["png", "jpg", "jpeg"], key=f"up_img_prod_{item_id}_{color_sel}")
                        if st.button("💾 Guardar Nueva Imagen", key=f"btn_save_img_{item_id}_{color_sel}"):
                            if nueva_img_file is not None:
                                try:
                                    url_subida = subir_a_supabase(nueva_img_file.getvalue(), nueva_img_file.name)
                                    dict_colores[color_sel]["imagen_url"] = url_subida
                                    supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                    st.success("✅ ¡Imagen actualizada con éxito!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al subir imagen: {e}")
                            else:
                                st.warning("Selecciona una imagen primero.")
                        
                        st.markdown("---")
                        st.markdown("#### ➕ Agregar Nuevo Color a este Producto")
                        col_nuevo_n, col_nuevo_hex = st.columns([2, 1])
                        with col_nuevo_n:
                            val_nuevo_c_nombre = st.text_input("Nombre del nuevo color", key=f"add_col_name_{item_id}")
                        with col_nuevo_hex:
                            val_nuevo_c_hex = st.color_picker("Color", "#3b82f6", key=f"add_col_hex_{item_id}")
                        
                        file_nuevo_c = st.file_uploader(f"Imagen para el nuevo color", type=["png", "jpg", "jpeg"], key=f"add_col_file_{item_id}")
                        
                        if st.button("➕ Añadir Color al Producto", key=f"btn_add_col_prod_{item_id}"):
                            c_clean_new = val_nuevo_c_nombre.strip()
                            if c_clean_new:
                                if c_clean_new not in dict_colores:
                                    url_new_col = ""
                                    if file_nuevo_c is not None:
                                        url_new_col = subir_a_supabase(file_nuevo_c.getvalue(), file_nuevo_c.name)
                                    
                                    dict_colores[c_clean_new] = {
                                        "tallas": {t: 0 for t in tallas_disponibles},
                                        "imagen_url": url_new_col,
                                        "hex": val_nuevo_c_hex
                                    }
                                    supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                    st.success(f"✅ Color '{c_clean_new}' añadido correctamente.")
                                    st.session_state[key_activo] = c_clean_new
                                    st.rerun()
                                else:
                                    st.warning("Este color ya existe en el producto.")
                            else:
                                st.error("Ingresa un nombre válido para el color.")

                        if len(dict_colores) > 1:
                            st.markdown("---")
                            st.markdown("#### 🗑️ Eliminar un Color")
                            color_a_borrar = st.selectbox("Selecciona color a eliminar", list(dict_colores.keys()), key=f"sel_del_col_{item_id}")
                            if st.button("🗑️ Eliminar Color Seleccionado", key=f"btn_del_col_{item_id}_{color_a_borrar}"):
                                del dict_colores[color_a_borrar]
                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                st.success(f"⚠️ Color '{color_a_borrar}' eliminado.")
                                st.session_state[key_activo] = list(dict_colores.keys())[0]
                                st.rerun()
                        else:
                            st.info("ℹ️ El producto debe tener al menos un color.")

                    if st.button("🗑️ Eliminar Producto Completo", key=f"del_prod_item_{item_id}"):
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
        st.subheader("👥 Gestión de Usuarios")
        with st.form("form_crear_usuario"):
            nuevo_user = st.text_input("Nombre de Usuario")
            nuevo_pass = st.text_input("Contraseña", type="password")
            nuevo_rol = st.selectbox("Rol Asignado", roles_disponibles)
            submit_user = st.form_submit_button("Crear Usuario")
            if submit_user:
                if nuevo_user and nuevo_pass:
                    try:
                        supabase.table("usuarios").insert({
                            "usuario": nuevo_user,
                            "password": nuevo_pass,
                            "rol_id": nuevo_rol
                        }).execute()
                        st.success("✅ Usuario creado exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear usuario: {e}")
                else:
                    st.warning("Completa todos los campos.")
        
        st.markdown("---")
        st.subheader("Lista de Usuarios Registrados")
        try:
            usuarios_db = supabase.table("usuarios").select("*").execute().data
            if usuarios_db:
                for u in usuarios_db:
                    col_u1, col_u2, col_u3 = st.columns([2, 2, 1])
                    with col_u1:
                        st.text(f"👤 {u.get('usuario')}")
                    with col_u2:
                        st.text(f"Rol: {u.get('rol_id')}")
                    with col_u3:
                        if st.button("🗑️", key=f"del_user_{u.get('id')}"):
                            supabase.table("usuarios").delete().eq("id", u.get('id')).execute()
                            st.success("Usuario eliminado")
                            st.rerun()
            else:
                st.info("No hay usuarios adicionales registrados.")
        except Exception as e:
            st.error(f"Error al cargar usuarios: {e}")
    else:
        st.warning("⚠️ No tienes permisos para acceder a esta sección.")
