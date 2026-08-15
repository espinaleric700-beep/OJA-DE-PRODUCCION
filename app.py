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
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

roles_disponibles = [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión"
]

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
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Usuarios"])

# ------------------------------------------
# TAB 0: VER Y FILTRAR ÓRDENES
# ------------------------------------------
with tabs[0]:
    st.subheader("📋 Listado y Control de Órdenes")
    try:
        ordenes = supabase.table("ordenes").select("*").execute().data
        lista_estados = ["Pendiente", "Enviado a Recepción", "En Producción", "Regresado a Recepción", "Orden Entregada"]
        
        estados_filtro = st.multiselect("Filtrar por estado:", lista_estados, default=[])
        
        if ordenes:
            ordenes_a_mostrar = [o for o in ordenes if (o.get('estado') or o.get('estado_actual')) in estados_filtro] if estados_filtro else ordenes
            
            for o in ordenes_a_mostrar:
                estado_actual = o.get('estado') or o.get('estado_actual') or 'Pendiente'
                
                with st.expander(f"Orden #{o.get('numero_orden', 'N/A')} - Cliente: {o.get('nombre_cliente', 'N/A')} | Estado: {estado_actual}"):
                    st.write(f"**Área:** {o.get('area_produccion', 'N/A')} | **Detalles:** {o.get('nombre_orden', 'N/A')}")
                    
                    # Formulario para actualizar estado
                    with st.form(f"form_update_{o.get('id')}"):
                        nuevo_estado = st.selectbox(
                            f"Cambiar estado #{o.get('numero_orden')}", 
                            lista_estados, 
                            index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0, 
                            key=f"sel_{o.get('id')}"
                        )
                        
                        if st.form_submit_button("💾 Actualizar y Registrar Cambio"):
                            # 1. Actualizar estado en la tabla de órdenes
                            supabase.table("ordenes").update({
                                "estado": nuevo_estado, 
                                "estado_actual": nuevo_estado
                            }).eq("id", o.get("id")).execute()
                            
                            # 2. Registrar en el historial de cambios
                            supabase.table("historial_ordenes").insert({
                                "orden_id": str(o.get('id')),
                                "nuevo_estado": nuevo_estado,
                                "usuario_que_cambio": st.session_state['usuario'],
                                "fecha_hora": datetime.now().isoformat()
                            }).execute()
                            
                            st.success("✅ Estado actualizado y registrado correctamente.")
                            st.rerun()

                    if o.get('factura_url'):
                        st.markdown(f"📄 [Ver Factura]({o.get('factura_url')})")

                    # 3. Desplegable con el historial de cambios
                    with st.expander("🕒 Ver historial de cambios de estado"):
                        try:
                            historial = supabase.table("historial_ordenes").select("*").eq("orden_id", str(o.get('id'))).order("fecha_hora", desc=True).execute().data
                            if historial:
                                for h in historial:
                                    fecha_formateada = h['fecha_hora'][:16].replace('T', ' ') if h.get('fecha_hora') else 'N/A'
                                    st.write(f"- **{h.get('nuevo_estado')}** | Modificado por: `{h.get('usuario_que_cambio')}` | Fecha: {fecha_formateada}")
                            else:
                                st.info("No hay cambios registrados en el historial para esta orden.")
                        except Exception as e:
                            st.warning("No se pudo cargar el historial (verifica que la tabla 'historial_ordenes' exista en Supabase).")
        else:
            st.info("No hay órdenes registradas.")
    except Exception as e:
        st.error(f"Error al cargar órdenes: {e}")

# ------------------------------------------
# TAB 1: NUEVA ORDEN
# ------------------------------------------
with tabs[1]:
    with st.form("form_nueva_orden", clear_on_submit=True):
        cliente = st.text_input("Nombre del Cliente")
        nombre_ord = st.text_input("Nombre de la Orden / Detalles")
        area = st.selectbox("Área", ["Bordados", "Impresion"])
        archivos = st.file_uploader("Subir Archivos", accept_multiple_files=True)
        
        if st.form_submit_button("Guardar Orden"):
            try:
                urls = [subir_a_supabase(a.getvalue(), a.name) for a in archivos] if archivos else []
                num_auto = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                supabase.table("ordenes").insert({
                    "numero_orden": num_auto,
                    "nombre_cliente": cliente,
                    "nombre_orden": nombre_ord,
                    "area_produccion": area,
                    "imagen_url": ",".join(urls),
                    "estado": "Pendiente",
                    "estado_actual": "Pendiente"
                }).execute()
                st.success("✅ Orden creada con éxito.")
            except Exception as e:
                st.error(f"Error: {e}")

# ------------------------------------------
# TAB 2: GESTIÓN DE USUARIOS (ADMIN)
# ------------------------------------------
with tabs[2]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Registrar Nuevo Usuario")
        with st.form("reg_user", clear_on_submit=True):
            n_nombre = st.text_input("Nombre Completo")
            n_user = st.text_input("Nombre de Usuario")
            n_pass = st.text_input("Contraseña", type="password")
            n_rol = st.selectbox("Rol Asignado", roles_disponibles)
            
            if st.form_submit_button("Guardar Usuario"):
                try:
                    supabase.table("usuarios").insert({
                        "nombre": n_nombre, 
                        "usuario": n_user, 
                        "password": n_pass, 
                        "rol_id": n_rol
                    }).execute()
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
        st.error("⛔ Acceso restringido. Esta sección es exclusiva para Administradores.")
