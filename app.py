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
    .stButton > button { border-radius: 6px; border: none; font-weight: 600; padding: 0.2rem 0.4rem; width: 100%; min-height: 1.8rem; margin-top: 0rem; }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

roles_disponibles = [
    "Administrador", 
    "Recepción", 
    "Diseñador", 
    "Almacén", 
    "Producción - Bordados", 
    "Producción - Impresión", 
    "Producción - Transferencia Térmica"
]

lista_estados = [
    "Pendiente", 
    "Recepción", 
    "Producción - Bordados", 
    "Producción - Impresión", 
    "Producción - Transferencia Térmica", 
    "Orden Detenida",
    "Orden Cancelada",
    "Orden Entregada"
]

tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL"]

def limpiar_nombre_archivo(nombre):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    nombre_seguro = limpiar_nombre_archivo(file_name)
    path = f"almacen/{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if "colores_inventario_avanzado" not in st.session_state:
    st.session_state["colores_inventario_avanzado"] = {}

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
                else:
                    st.sidebar.error("❌ Usuario o contraseña incorrectos.")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    st.stop()

st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.sidebar.info(f"👤 Usuario: **{st.session_state['usuario']}** | Rol: **{st.session_state['rol']}**")

st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

with tabs[0]:
    st.subheader("📋 Listado y Control de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        estados_filtro = st.multiselect("Filtrar por estado:", lista_estados, default=[])
        
        if ordenes:
            ordenes_a_mostrar = [o for o in ordenes if (o.get('estado') or o.get('estado_actual')) in estados_filtro] if estados_filtro else ordenes
            for o in ordenes_a_mostrar:
                estado_actual = o.get('estado') or o.get('estado_actual') or 'Pendiente'
                
                color_map = {
                    "Pendiente": "🟡",
                    "Recepción": "🔵",
                    "Producción - Bordados": "🟠",
                    "Producción - Impresión": "🟣",
                    "Producción - Transferencia Térmica": "🟤",
                    "Orden Detenida": "⚠️",
                    "Orden Cancelada": "❌",
                    "Orden Entregada": "🟢"
                }
                icono_estado = color_map.get(estado_actual, "⚪")

                col_izq, col_der = st.columns([3, 1])
                with col_izq:
                    contacto_str = f" | 📞 Contacto: {o.get('contacto_cliente')}" if o.get('contacto_cliente') else ""
                    with st.expander(f"{icono_estado} Orden #{o.get('numero_orden', 'N/A')} - Cliente: {o.get('nombre_cliente', 'N/A')}{contacto_str} | Estado: {estado_actual}"):
                        st.write(f"**Área:** {o.get('area_produccion', 'N/A')} | **Detalles:** {o.get('nombre_orden', 'N/A')}")
                        if o.get('contacto_cliente'):
                            st.write(f"**Contacto del Cliente:** {o.get('contacto_cliente')}")
                        if o.get('factura_url'): st.markdown(f"📄 [Ver Factura]({o.get('factura_url')})")
                with col_der:
                    with st.form(f"form_quick_{o.get('id')}"):
                        nuevo_estado = st.selectbox("Cambiar", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0, label_visibility="collapsed")
                        if st.form_submit_button("Actualizar"):
                            supabase.table("ordenes").update({"estado": nuevo_estado, "estado_actual": nuevo_estado}).eq("id", o.get("id")).execute()
                            st.rerun()
        else: st.info("No hay órdenes.")
    except Exception as e: st.error(f"Error: {e}")

with tabs[1]:
    with st.form("form_nueva_orden", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente")
        contacto = st.text_input("Contacto del Cliente (Teléfono / Email)")
        nombre_ord = st.text_input("Nombre de la Orden")
        area = st.selectbox("Área", roles_disponibles[4:])
        fecha_entrega = st.date_input("Fecha de Entrega")
        if st.form_submit_button("Guardar Orden"):
            num_auto = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            supabase.table("ordenes").insert({
                "numero_orden": num_auto, 
                "nombre_cliente": cliente, 
                "contacto_cliente": contacto,
                "nombre_orden": nombre_ord,
                "area_produccion": area, 
                "fecha_entrega": str(fecha_entrega), 
                "estado": "Pendiente", 
                "estado_actual": "Pendiente"
            }).execute()
            st.success("✅ Orden creada.")

with tabs[2]:
    st.subheader("📦 Control de Inventario y Almacén")
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Nuevo Producto con Colores, Tallas e Imagen por Color", expanded=False):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA (Ej. TSHIRT ALGODON)", key="input_nombre_prenda_color_img")
            
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
                        st.success("✅ ¡Producto con imágenes por color guardado con éxito!")
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
                p_tallas_str = item.get("tallas_existencias", "")
                p_imagen_general = item.get("imagen_url", "")

                dict_colores = {}
                es_avanzado = False
                try:
                    dict_colores = json.loads(p_tallas_str)
                    if isinstance(dict_colores, dict):
                        primer_valor = next(iter(dict_colores.values())) if dict_colores else None
                        if isinstance(primer_valor, dict) and "tallas" in primer_valor:
                            es_avanzado = True
                except:
                    pass

                with st.container():
                    st.markdown(f"### 🏷️ {p_nombre}")
                    
                    if es_avanzado and dict_colores:
                        lista_cols = list(dict_colores.keys())
                        
                        key_activo = f"color_activo_btn_{item_id}"
                        if key_activo not in st.session_state or st.session_state[key_activo] not in lista_cols:
                            st.session_state[key_activo] = lista_cols[0]

                        st.markdown("Colores")

                        # Forzamos mediante CSS que cada botón tenga exactamente el color HEX de fondo registrado
                        css_botones_dinamicos = ""
                        for idx_c, c_name in enumerate(lista_cols):
                            c_hex = dict_colores[c_name].get("hex", "#3b82f6")
                            es_seleccionado = (st.session_state[key_activo] == c_name)
                            borde_estilo = "3px solid #ffffff" if es_seleccionado else "1px solid rgba(255, 255, 255, 0.3)"
                            
                            css_botones_dinamicos += f"""
                            div[data-testid="column"]:has(button#btn_col_{item_id}_{idx_c}) button {{
                                background-color: {c_hex} !important;
                                color: #ffffff !important;
                                border: {borde_estilo} !important;
                                font-weight: bold !important;
                                text-shadow: 0px 1px 2px rgba(0,0,0,0.6);
                            }}
                            """
                        st.markdown(f"<style>{css_botones_dinamicos}</style>", unsafe_allow_html=True)

                        # Renderizamos los botones con su respectivo índice numérico interno para evitar colisiones de IDs en Streamlit
                        cols_botones = st.columns(len(lista_cols))
                        for i, c_name in enumerate(lista_cols):
                            with cols_botones[i]:
                                if st.button(c_name, key=f"btn_col_{item_id}_{i}", use_container_width=True):
                                    st.session_state[key_activo] = c_name
                                    st.rerun()

                        color_seleccionado_ver = st.session_state[key_activo]
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        col_img, col_info = st.columns([1, 3])
                        
                        if color_seleccionado_ver:
                            info_color_actual = dict_colores[color_seleccionado_ver]
                            img_url_color = info_color_actual.get("imagen_url", "")
                            tallas_del_color = info_color_actual.get("tallas", {})
                            
                            with col_img:
                                if img_url_color:
                                    st.image(img_url_color, use_container_width=True)
                                else:
                                    st.info("Sin foto para este color")
                                    
                            with col_info:
                                cols_por_fila = 3
                                tallas_items = [(t, tallas_del_color.get(t, 0)) for t in tallas_disponibles]
                                st.markdown(f"**Existencias para el color: `{color_seleccionado_ver}`**")
                                for i in range(0, len(tallas_items), cols_por_fila):
                                    fila_cols = st.columns(cols_por_fila)
                                    for j in range(cols_por_fila):
                                        if i + j < len(tallas_items):
                                            talla, cantidad = tallas_items[i + j]
                                            with fila_cols[j]:
                                                if puede_modificar:
                                                    sub_c_btn1, sub_c_txt, sub_c_btn2 = st.columns([0.6, 2, 0.6], gap="small")
                                                    with sub_c_btn1:
                                                        if st.button("➖", key=f"m_av_{item_id}_{color_seleccionado_ver}_{talla}"):
                                                            if cantidad > 0:
                                                                dict_colores[color_seleccionado_ver]["tallas"][talla] = cantidad - 1
                                                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                                                st.rerun()
                                                    with sub_c_txt:
                                                        st.markdown(f"<div style='background-color: #111827; padding: 4px 2px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='font-size: 0.8em; font-weight: bold;'>{talla}</span><br><span style='font-size: 0.85em; color: #60a5fa;'>{cantidad}</span></div>", unsafe_allow_html=True)
                                                    with sub_c_btn2:
                                                        if st.button("➕", key=f"p_av_{item_id}_{color_seleccionado_ver}_{talla}"):
                                                            dict_colores[color_seleccionado_ver]["tallas"][talla] = cantidad + 1
                                                            supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                                            st.rerun()
                                                else:
                                                    st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 6px; border: 1px solid #1f2937; text-align: center;'><b>{talla}</b><br><span style='color: #60a5fa;'>{cantidad}</span></div>", unsafe_allow_html=True)
                    else:
                        col_img, col_info = st.columns([1, 3])
                        with col_img:
                            if p_imagen_general:
                                st.image(p_imagen_general, use_container_width=True)
                            else:
                                st.info("Sin foto disponible")
                        with col_info:
                            st.write(f"**Tallas/Existencias:** {p_tallas_str}")

                    if puede_modificar:
                        with st.expander("🛠️ Opciones Avanzadas (Eliminar producto)"):
                            if st.button("🗑️ Eliminar Producto", key=f"del_prod_{item_id}"):
                                try:
                                    supabase.table("almacen").delete().eq("id", item_id).execute()
                                    st.warning("⚠️ Producto eliminado del inventario.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error al eliminar: {ex}")
                    st.divider()
        else:
            st.info("No hay productos registrados en el almacén.")
    except Exception as e:
        st.error(f"Error al cargar el almacén: {e}")

with tabs[3]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Registrar Nuevo Usuario")
        with st.form("reg_user", clear_on_submit=True):
            n_nombre = st.text_input("Nombre Completo")
            n_user = st.text_input("Nombre de Usuario")
            n_pass = st.text_input("Contraseña", type="password")
            n_rol = st.selectbox("Rol Asignado", roles_disponibles)
            if st.form_submit_button("Guardar Usuario"):
                try:
                    supabase.table("usuarios").insert({"nombre": n_nombre, "usuario": n_user, "password": n_pass, "rol_id": n_rol}).execute()
                    st.success("✅ Usuario creado con éxito.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear usuario: {e}")

        st.divider()
        st.subheader("🛠️ Usuarios Existentes (Modificar / Eliminar)")
        
        try:
            usuarios_db = supabase.table("usuarios").select("*").execute().data
            if usuarios_db:
                for u in usuarios_db:
                    u_id = u.get("id")
                    u_nombre = u.get("nombre", "")
                    u_username = u.get("usuario", "")
                    u_pass = u.get("password", "")
                    u_rol = u.get("rol_id", "Recepción")
                    
                    with st.expander(f"👤 {u_nombre} (`{u_username}`) - Rol: **{u_rol}**"):
                        with st.form(f"form_edit_{u_id}"):
                            edit_nombre = st.text_input("Nombre", value=u_nombre, key=f"n_{u_id}")
                            edit_user = st.text_input("Usuario", value=u_username, key=f"usr_{u_id}")
                            edit_pass = st.text_input("Contraseña", value=u_pass, type="password", key=f"p_{u_id}")
                            
                            idx_rol = roles_disponibles.index(u_rol) if u_rol in roles_disponibles else 0
                            edit_rol = st.selectbox("Rol", roles_disponibles, index=idx_rol, key=f"r_{u_id}")
                            
                            col1, col2 = st.columns(2)
                            actualizar = col1.form_submit_button("💾 Guardar Cambios")
                            eliminar = col2.form_submit_button("🗑️ Eliminar Usuario")
                            
                            if actualizar:
                                try:
                                    supabase.table("usuarios").update({
                                        "nombre": edit_nombre,
                                        "usuario": edit_user,
                                        "password": edit_pass,
                                        "rol_id": edit_rol
                                    }).eq("id", u_id).execute()
                                    st.success("✅ Usuario actualizado correctamente.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error al actualizar: {ex}")
                                    
                            if eliminar:
                                try:
                                    supabase.table("usuarios").delete().eq("id", u_id).execute()
                                    st.warning("⚠️ Usuario eliminado.")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"Error al eliminar: {ex}")
            else:
                st.info("No hay usuarios registrados en la base de datos.")
        except Exception as e:
            st.error(f"Error al cargar la lista de usuarios: {e}")
    else: 
        st.error("⛔ Acceso Restringido.")
