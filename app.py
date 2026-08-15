from datetime import datetime
import streamlit as st
from supabase import create_client
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURACIÓN Y ESTILO VISUAL (MODO OSCURO)
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Actualización automática cada 10 segundos
st_autorefresh(interval=10000, key="auto_refresh_ordenes")

st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    div.streamlit-expanderHeader { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; color: #f9fafb; font-weight: 600; }
    div[data-testid="stForm"] { background-color: #111827; border: 1px solid #374151; border-radius: 10px; padding: 10px; }
    p, label, span, div { color: #e5e7eb; }
    .stButton > button { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border-radius: 6px; border: none; font-weight: 600; padding: 0.2rem 0.4rem; width: 100%; min-height: 1.8rem; margin-top: 0rem; }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
    [data-testid="column"] { padding: 0px 2px !important; }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# ROLES Y ESTADOS DISPONIBLES
# ==========================================
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

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"almacen/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==========================================
# GESTIÓN DE SESIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

if "tallas_temp" not in st.session_state:
    st.session_state["tallas_temp"] = {}

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

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.sidebar.info(f"👤 Usuario: **{st.session_state['usuario']}** | Rol: **{st.session_state['rol']}**")

st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

# ------------------------------------------
# TAB 0: VER Y FILTRAR ÓRDENES
# ------------------------------------------
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

# ------------------------------------------
# TAB 1: NUEVA ORDEN
# ------------------------------------------
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

# ------------------------------------------
# TAB 2: ALMACÉN E INVENTARIO
# ------------------------------------------
with tabs[2]:
    st.subheader("📦 Control de Inventario y Almacén")
    
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Nuevo Producto al Inventario", expanded=False):
            inv_nombre = st.text_input("AGREGAR NOMBRE (Ej. TSHIRT ALGODON)", key="input_nombre_prenda")
            color_prenda = st.text_input("AGREGAR COLOR (Ej. #FF00FF o Fucsia)", key="input_color_prenda")
            foto_prenda = st.file_uploader("SUBIR IMAGEN DE PRENDA", type=["png", "jpg", "jpeg"], key="input_foto_prenda")
            
            st.markdown("---")
            st.markdown("#### 📏 Tallas y Existencias:")
            
            cols_grid = st.columns(3)
            for idx, talla in enumerate(tallas_disponibles):
                col_actual = cols_grid[idx % 3]
                with col_actual:
                    val_actual = st.session_state["tallas_temp"].get(talla, 0)
                    nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=val_actual, key=f"temp_t_{talla}")
                    st.session_state["tallas_temp"][talla] = int(nueva_cant)

            st.markdown("---")
            if st.button("💾 Guardar Inventario Completo"):
                if not inv_nombre.strip():
                    st.error("⚠️ Debes ingresar el nombre del producto.")
                else:
                    try:
                        tallas_str = ", ".join([f"{t}: {c}" for t, c in st.session_state["tallas_temp"].items()])
                        
                        foto_url = ""
                        if foto_prenda:
                            foto_url = subir_a_supabase(foto_prenda.getvalue(), foto_prenda.name)
                        
                        supabase.table("almacen").insert({
                            "nombre_producto": inv_nombre,
                            "tallas_existencias": tallas_str,
                            "imagen_url": foto_url
                        }).execute()
                        
                        st.session_state["tallas_temp"] = {}
                        st.success("✅ ¡Producto guardado en el inventario con éxito!")
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
                p_imagen = item.get("imagen_url", "")

                dict_tallas = {}
                if p_tallas_str:
                    for part in p_tallas_str.split(","):
                        if ":" in part:
                            t_key, t_val = part.split(":", 1)
                            try:
                                dict_tallas[t_key.strip()] = int(t_val.strip())
                            except:
                                pass

                with st.container():
                    st.markdown(f"### 🏷️ {p_nombre}")
                    col_img, col_info = st.columns([1, 3])
                    
                    with col_img:
                        if p_imagen:
                            st.image(p_imagen, use_container_width=True)
                        else:
                            st.info("Sin foto disponible")
                            
                    with col_info:
                        st.markdown("#### 📏 Tallas y Existencias:")
                        
                        if dict_tallas:
                            cols_por_fila = 3
                            tallas_items = [(t, dict_tallas.get(t, 0)) for t in tallas_disponibles]
                            
                            for i in range(0, len(tallas_items), cols_por_fila):
                                fila_cols = st.columns(cols_por_fila)
                                for j in range(cols_por_fila):
                                    if i + j < len(tallas_items):
                                        talla, cantidad = tallas_items[i + j]
                                        with fila_cols[j]:
                                            if puede_modificar:
                                                sub_c_btn1, sub_c_txt, sub_c_btn2 = st.columns([0.6, 2, 0.6], gap="small")
                                                with sub_c_btn1:
                                                    if st.button("➖", key=f"m_{item_id}_{talla}"):
                                                        if cantidad > 0:
                                                            dict_tallas[talla] = cantidad - 1
                                                            nuevo_str = ", ".join([f"{tk}: {tv}" for tk, tv in dict_tallas.items()])
                                                            supabase.table("almacen").update({"tallas_existencias": nuevo_str}).eq("id", item_id).execute()
                                                            st.rerun()
                                                with sub_c_txt:
                                                    st.markdown(f"<div style='background-color: #111827; padding: 4px 2px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='font-size: 0.8em; font-weight: bold;'>{talla}</span><br><span style='font-size: 0.85em; color: #60a5fa;'>{cantidad}</span></div>", unsafe_allow_html=True)
                                                with sub_c_btn2:
                                                    if st.button("➕", key=f"p_{item_id}_{talla}"):
                                                        dict_tallas[talla] = cantidad + 1
                                                        nuevo_str = ", ".join([f"{tk}: {tv}" for tk, tv in dict_tallas.items()])
                                                        supabase.table("almacen").update({"tallas_existencias": nuevo_str}).eq("id", item_id).execute()
                                                        st.rerun()
                                            else:
                                                st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 6px; border: 1px solid #1f2937; text-align: center;'><b>{talla}</b><br><span style='color: #60a5fa;'>{cantidad}</span></div>", unsafe_allow_html=True)
                        else:
                            st.info("No hay tallas definidas.")
                        
                        if puede_modificar:
                            with st.expander("🛠️ Opciones Avanzadas (Editar texto completo o Eliminar producto)"):
                                with st.form(f"form_edit_inv_{item_id}"):
                                    edit_nombre = st.text_input("Nombre de la Prenda", value=p_nombre, key=f"inv_n_{item_id}")
                                    edit_tallas = st.text_area("Tallas y Cantidades (Formato: S: 10, M: 15)", value=p_tallas_str, key=f"inv_t_{item_id}")
                                    
                                    col_act, col_del = st.columns(2)
                                    btn_act = col_act.form_submit_button("💾 Guardar Cambios")
                                    btn_del = col_del.form_submit_button("🗑️ Eliminar Producto")
                                    
                                    if btn_act:
                                        try:
                                            supabase.table("almacen").update({
                                                "nombre_producto": edit_nombre,
                                                "tallas_existencias": edit_tallas
                                            }).eq("id", item_id).execute()
                                            st.success("✅ Inventario actualizado.")
                                            st.rerun()
                                        except Exception as ex:
                                            st.error(f"Error al actualizar: {ex}")
                                            
                                    if btn_del:
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

# ------------------------------------------
# TAB 3: GESTIÓN DE USUARIOS (ADMIN)
# ------------------------------------------
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
        st.error("⛔ Acceso restringido.")
