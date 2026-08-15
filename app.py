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

roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión"]

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
        try:
            res = supabase.table("usuarios").select("*").execute()
            usuario_encontrado = next((u for u in res.data if u["usuario"].lower() == usuario_input.lower() and u["password"] == password_input), None)
            if usuario_encontrado:
                st.session_state.update({"autenticado": True, "usuario": usuario_input, "rol": usuario_encontrado.get("rol_id", "")})
                st.rerun()
            else:
                st.sidebar.error("❌ Credenciales incorrectas.")
        except Exception as e: st.sidebar.error(f"Error: {e}")
    st.stop()

st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Usuarios"])

# ------------------------------------------
# TAB 0: VER Y FILTRAR ÓRDENES
# ------------------------------------------
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    ordenes = supabase.table("ordenes").select("*").execute().data
    lista_estados = ["Pendiente", "Enviado a Recepción", "En Producción", "Regresado a Recepción", "Orden Entregada"]
    
    for o in ordenes:
        estado_actual = o.get('estado', 'Pendiente')
        with st.expander(f"Orden #{o.get('numero_orden')} - Cliente: {o.get('nombre_cliente')} | Estado: {estado_actual}"):
            st.write(f"**Área:** {o.get('area_produccion')}")
            
            # Formulario de actualización
            with st.form(f"form_update_{o.get('id')}"):
                nuevo_estado = st.selectbox("Cambiar estado", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0)
                if st.form_submit_button("💾 Actualizar y Registrar Cambio"):
                    # 1. Actualizar estado
                    supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", o.get("id")).execute()
                    
                    # 2. Registrar en historial
                    supabase.table("historial_ordenes").insert({
                        "orden_id": str(o.get('id')), # Aseguramos que sea string
                        "nuevo_estado": nuevo_estado,
                        "usuario_que_cambio": st.session_state['usuario'],
                        "fecha_hora": datetime.now().isoformat()
                    }).execute()
                    st.success("✅ Estado actualizado y registrado.")
                    st.rerun()
            
            # Desplegable del historial
            with st.expander("🕒 Ver historial de cambios"):
                historial = supabase.table("historial_ordenes").select("*").eq("orden_id", str(o.get('id'))).order("fecha_hora", desc=True).execute().data
                if historial:
                    for h in historial:
                        st.write(f"- **{h['nuevo_estado']}** | Por: {h['usuario_que_cambio']} | el {h['fecha_hora'][:16].replace('T', ' ')}")
                else:
                    st.info("Sin historial.")

# ------------------------------------------
# TAB 1: NUEVA ORDEN
# ------------------------------------------
with tabs[1]:
    with st.form("form_nueva_orden", clear_on_submit=True):
        cliente = st.text_input("Cliente")
        nombre_ord = st.text_input("Detalles")
        area = st.selectbox("Área", ["Bordados", "Impresion"])
        if st.form_submit_button("Guardar"):
            supabase.table("ordenes").insert({"numero_orden": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}", "nombre_cliente": cliente, "nombre_orden": nombre_ord, "area_produccion": area, "estado": "Pendiente"}).execute()
            st.success("✅ Orden creada.")

# ------------------------------------------
# TAB 2: GESTIÓN DE USUARIOS
# ------------------------------------------
with tabs[2]:
    if st.session_state['rol'] == "Administrador":
        # ... (Tu código anterior de gestión de usuarios) ...
        st.write("Panel de administrador activo.")
    else:
        st.error("Acceso restringido.")
