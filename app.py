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
    .stButton > button { border-radius: 4px; border: none; font-weight: 600; padding: 0.3rem 0.6rem; min-height: 2rem; font-size: 0.8rem; }
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
    except Exception: pass
    return "0000001"

def actualizar_estado_con_historial(o_id, estado_anterior, nuevo_estado, historial_actual, usuario_actual):
    if nuevo_estado == estado_anterior: return
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_registro = {"usuario": usuario_actual, "de": estado_anterior, "a": nuevo_estado, "fecha": ahora}
    lista_historial = []
    if historial_actual:
        if isinstance(historial_actual, str):
            try: lista_historial = json.loads(historial_actual)
            except: lista_historial = []
        elif isinstance(historial_actual, list): lista_historial = historial_actual
    lista_historial.insert(0, nuevo_registro)
    supabase.table("ordenes").update({"estado": nuevo_estado, "historial": json.dumps(lista_historial)}).eq("id", o_id).execute()

# Estado global inicial
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})
if "colores_inventario_avanzado" not in st.session_state: st.session_state["colores_inventario_avanzado"] = {}

# --- Autenticación ---
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
            else: st.sidebar.error("❌ Usuario o contraseña incorrectos.")
        except Exception as e: st.sidebar.error(f"Error: {e}")
    st.stop()

st.sidebar.button("🚪 Cerrar Sesión", on_click=lambda: st.session_state.update({"autenticado": False}))
st.title("🧵 Pixel Thread - Gestión")
tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

# --- Tabs ---
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        busqueda = st.text_input("🔍 Buscar por Nombre de Cliente o # de Orden", placeholder="Ej: 0000001 o Juan Perez")
    with col_f2:
        filtro_estado = st.selectbox("Filtrar por Estado", ["Todos"] + lista_estados, key="filtro_estado_ordenes")
    
    try:
        query_ordenes = supabase.table("ordenes").select("*")
        if filtro_estado != "Todos": query_ordenes = query_ordenes.eq("estado", filtro_estado)
        ordenes = query_ordenes.execute().data
        
        if busqueda:
            termino = busqueda.lower()
            ordenes = [o for o in ordenes if termino in str(o.get("numero_orden", "")).lower() or termino in o.get("nombre_cliente", "").lower()]
        
        if ordenes:
            for o in ordenes:
                o_id = o.get("id"); numero_o = o.get('numero_orden', 'S/N'); cliente_o = o.get('nombre_cliente', 'Sin cliente'); estado_actual = o.get('estado', 'Pendiente'); historial_db = o.get('historial', "[]")
                col_res, col_act = st.columns([2, 2])
                with col_res: st.markdown(f"**Orden #{numero_o}** - {cliente_o} [Estado: *{estado_actual}*]")
                with col_act:
                    cols_action = st.columns([2, 1])
                    idx_actual = lista_estados.index(estado_actual) if estado_actual in lista_estados else 0
                    with cols_action[0]: nuevo_estado_sel = st.selectbox("Cambiar", lista_estados, index=idx_actual, key=f"sel_quick_{o_id}", label_visibility="collapsed")
                    with cols_action[1]:
                        if st.button("Cambiar Estado", key=f"btn_quick_{o_id}"):
                            if nuevo_estado_sel != estado_actual:
                                actualizar_estado_con_historial(o_id, estado_actual, nuevo_estado_sel, historial_db, st.session_state['usuario'])
                                st.rerun()
                with st.expander("Ver detalles completos"):
                    st.write(f"**Teléfono:** {o.get('telefono', 'N/D')} | **Fecha Entrega:** {o.get('fecha_entrega', 'N/D')}")
                    st.write(f"**Total:** ${o.get('total', 0)} | **Restante:** ${o.get('restante', 0)}")
                    st.markdown("📜 **Historial:**")
                    try:
                        registros = json.loads(historial_db) if isinstance(historial_db, str) else historial_db
                        for reg in registros[:5]: st.caption(f"🕒 {reg.get('fecha')} | {reg.get('de')} ➡️ {reg.get('a')}")
                    except: pass
                st.divider()
        else: st.info("No se encontraron órdenes.")
    except Exception as e: st.error(f"Error: {e}")

with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    numero_auto = obtener_siguiente_numero_orden()
    with st.form("form_crear_orden_completa"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.text_input("Número de Orden", value=numero_auto, disabled=True)
            nombre_cliente = st.text_input("Nombre del Cliente")
            telefono_cliente = st.text_input("Teléfono del Cliente")
        with col_c2:
            tipo_servicio = st.selectbox("Tipo de Servicio", ["Bordado", "DTF", "Sublimación", "Mixto"])
            fecha_entrega = st.date_input("Fecha Estimada de Entrega")
        total_orden = st.number_input("Total ($)", min_value=0.0, step=100.0)
        abono_orden = st.number_input("Abono ($)", min_value=0.0, step=100.0)
        if st.form_submit_button("💾 Guardar"):
            historial_inicial = json.dumps([{"usuario": st.session_state['usuario'], "de": "Inicio", "a": "Pendiente", "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
            supabase.table("ordenes").insert({"numero_orden": numero_auto, "nombre_cliente": nombre_cliente, "telefono": telefono_cliente, "tipo_servicio": tipo_servicio, "fecha_entrega": str(fecha_entrega), "total": total_orden, "abono": abono_orden, "restante": total_orden - abono_orden, "estado": "Pendiente", "historial": historial_inicial}).execute()
            st.rerun()

with tabs[2]:
    # (El código del almacén se mantiene igual, omitido por brevedad en esta respuesta)
    st.info("Pestaña de Almacén activa.")

with tabs[3]:
    if st.session_state['rol'] == "Administrador":
        st.subheader("👥 Gestión de Usuarios")
        # (Código de usuarios igual)
    else: st.warning("No tienes permisos.")
