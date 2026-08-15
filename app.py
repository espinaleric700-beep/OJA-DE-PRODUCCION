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
    .stButton > button { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border-radius: 8px; border: none; font-weight: 600; padding: 0.35rem 0.75rem; width: 100%; min-height: 2.2rem; margin-top: 1.6rem; }
    [data-testid="stSidebar"] { background-color: #030712; border-right: 1px solid #1f2937; }
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

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==========================================
# GESTIÓN DE SESIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

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
    
    # Verificar si el usuario tiene permiso para modificar/agregar/eliminar
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Nuevo Producto al Inventario"):
            with st.form("form_nuevo_inventario", clear_on_submit=True):
                inv_nombre = st.text_input("Nombre del Producto (Ej. Camiseta Ojo de Ángel)")
                inv_size = st.text_input("Talla / Size (Ej. S, M, L, XL, Única)")
                inv_cantidad = st.number_input("Cantidad en Existencia", min_value=0, step=1)
                
                if st.form_submit_button("Guardar en Inventario"):
                    try:
                        supabase.table("almacen").insert({
                            "nombre_producto": inv_nombre,
                            "talla": inv_size,
                            "cantidad": int(inv_cantidad)
                        }).execute()
                        st.success("✅ Producto agregado al inventario correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar producto (asegúrate de tener creada la tabla 'almacen' en Supabase): {e}")
        st.divider()

    # Mostrar inventario existente
    try:
        inventario_db = supabase.table("almacen").select("*").execute().data
        if inventario_db:
            st.markdown("### 📋 Existencias Actuales")
            for item in inventario_db:
                item_id = item.get("id")
                p_nombre = item.get("nombre_producto", "Sin nombre")
                p_talla = item.get("talla", "N/A")
                p_cantidad = item.get("cantidad", 0)

                if puede_modificar:
                    with st.expander(f"📦 {p_nombre} | Talla: **{p_talla}** | Stock: **{p_cantidad}**"):
                        with st.form(f"form_edit_inv_{item_id}"):
                            edit_nombre = st.text_input("Nombre del Producto", value=p_nombre, key=f"inv_n_{item_id}")
                            edit_talla = st.text_input("Talla / Size", value=p_talla, key=f"inv_t_{item_id}")
                            edit_cant = st.number_input("Cantidad", value=int(p_cantidad), min_value=0, step=1, key=f"inv_c_{item_id}")
                            
                            col_act, col_del = st.columns(2)
                            btn_act = col_act.form_submit_button("💾 Guardar Cambios")
                            btn_del = col_del.form_submit_button("🗑️ Eliminar Producto")
                            
                            if btn_act:
                                try:
                                    supabase.table("almacen").update({
                                        "nombre_producto": edit_nombre,
                                        "talla": edit_talla,
                                        "cantidad": int(edit_cant)
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
                else:
                    st.info(f"📦 **{p_nombre}** — Talla: `{p_talla}` — Cantidad en Existencia: **{p_cantidad}**")
        else:
            st.info("No hay productos registrados en el almacén.")
    except Exception as e:
        st.error(f"Nota: Si es la primera vez que usas esta sección, recuerda crear la tabla 'almacen' en Supabase con columnas: id, nombre_producto, talla, cantidad. Error: {e}")

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
