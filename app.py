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
        
        # --- FILTRO AGREGADO ---
        estados_filtro = st.multiselect("Filtrar por estado:", lista_estados, default=[])
        # -----------------------
        
        if ordenes:
            # Aplicar filtro si se seleccionó algo
            ordenes_a_mostrar = [o for o in ordenes if (o.get('estado') or o.get('estado_actual')) in estados_filtro] if estados_filtro else ordenes
            
            for o in ordenes_a_mostrar:
                estado_actual = o.get('estado') or o.get('estado_actual') or 'Pendiente'
                
                with st.expander(f"Orden #{o.get('numero_orden', 'N/A')} - Cliente: {o.get('nombre_cliente', 'N/A')} | Estado: {estado_actual}"):
                    st.write(f"**Área:** {o.get('area_produccion', 'N/A')} | **Detalles:** {o.get('nombre_orden', 'N/A')}")
                    
                    nuevo_estado = st.selectbox(f"Cambiar estado #{o.get('numero_orden')}", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0, key=f"sel_{o.get('id')}")
                    
                    if st.button("💾 Actualizar", key=f"btn_{o.get('id')}"):
                        supabase.table("ordenes").update({"estado": nuevo_estado, "estado_actual": nuevo_estado}).eq("id", o.get("id")).execute()
                        st.rerun()

                    if o.get('factura_url'):
                        st.markdown(f"📄 [Ver Factura]({o.get('factura_url')})")
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
                st.success("✅ Orden creada.")
            except Exception as e:
                st.error(f"Error: {e}")

# ------------------------------------------
# TAB 2: CONFIGURACIÓN
# ------------------------------------------
with tabs[2]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Registrar Usuario")
        with st.form("reg_user"):
            n_nombre = st.text_input("Nombre")
            n_user = st.text_input("Usuario")
            n_pass = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Guardar"):
                supabase.table("usuarios").insert({"nombre": n_nombre, "usuario": n_user, "password": n_pass, "rol_id": "Usuario"}).execute()
                st.success("Usuario creado")
    else:
        st.error("Acceso restringido a Administradores.")
