from datetime import datetime
import json
import re
import threading
import time
import urllib.request
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_js_eval import streamlit_js_eval
from supabase import create_client

# ==============================================================================
# MÓDULO AUTO-PING EN SEGUNDO PLANO
# ==============================================================================
URL_DE_MI_APP = "https://tu-app.streamlit.app"  # <--- Reemplaza con tu URL real

def keep_server_alive_loop(app_url, interval_seconds=300):
    time.sleep(10)
    while True:
        try:
            req = urllib.request.Request(
                app_url, 
                headers={'User-Agent': 'InternalKeepAlive/1.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
        except Exception:
            pass
        time.sleep(interval_seconds)

if "keep_alive_thread_started" not in st.session_state:
    st.session_state["keep_alive_thread_started"] = True
    ping_thread = threading.Thread(
        target=keep_server_alive_loop, 
        args=(URL_DE_MI_APP, 300),
        daemon=True
    )
    ping_thread.start()

# ==============================================================================
# CONFIGURACIÓN Y ESTILOS CSS ADAPTATIVOS
# ==============================================================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

components.html(
    """
    <script>
    const meta = document.createElement('meta');
    meta.name = 'viewport';
    meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    document.getElementsByTagName('head')[0].appendChild(meta);

    function keepAlive() {
        fetch(window.location.href, {mode: 'no-cors'}).catch((err) => {});
    }
    setInterval(keepAlive, 120000);
    </script>
    """,
    height=0,
    width=0
)

st.markdown("""
    <style>
    .stApp { 
        background-color: #0b0e14;
        background-image: 
            radial-gradient(circle at 50% 0%, rgba(88, 166, 255, 0.08) 0%, transparent 50%),
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 24px 24px, 24px 24px;
        background-attachment: fixed;
        color: #e6edf3; 
    }
    
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }

    /* Solución definitiva para evitar apertura accidental de selects y baseweb al hacer scroll táctil */
    select, [data-baseweb="select"], [data-baseweb="select"] *, div[data-baseweb="select"] div {
        touch-action: pan-y !important;
        -webkit-user-select: none;
        user-select: none;
    }
    
    .user-card {
        background-color: rgba(22, 27, 34, 0.85);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 0.85rem;
        backdrop-filter: blur(4px);
    }

    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        background-color: #161b22 !important;
        color: #ffffff !important;
        border: 1px solid #363b42 !important;
        width: 100%;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #21262d !important;
        color: #58a6ff !important;
        border-color: #58a6ff !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: rgba(22, 27, 34, 0.75) !important;
        border: 1px solid #30363d !important;
        border-left: 4px solid #58a6ff !important;
        border-radius: 10px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }

    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        align-items: center;
        background: transparent !important;
        border-radius: 0px !important;
        padding: 0px !important;
        border: none !important;
        box-shadow: none !important;
    }

    [data-testid="stImage"] img {
        mix-blend-mode: normal !important;
        filter: drop-shadow(0px 8px 16px rgba(0, 0, 0, 0.45));
    }

    div[data-testid="stNumberInput"] {
        background: rgba(22, 27, 34, 0.85);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 4px 6px;
        margin-bottom: 4px;
    }
    div[data-testid="stNumberInput"] label {
        font-size: 0.75rem !important;
        color: #8b949e !important;
        font-weight: 700;
        text-transform: uppercase;
    }
    div[data-testid="stNumberInput"] input {
        height: 32px !important;
        font-size: 0.88rem !important;
        background-color: transparent !important;
        color: #ffffff !important;
        text-align: center;
        border: none !important;
    }

    div[data-testid="stRadio"] > div {
        gap: 8px !important;
        flex-wrap: wrap !important;
        background: rgba(22, 27, 34, 0.85);
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }

    .sizes-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 8px;
        margin-bottom: 12px;
        font-size: 0.88rem;
    }
    .sizes-table th {
        background-color: rgba(88, 166, 255, 0.15);
        color: #58a6ff;
        border: 1px solid #30363d;
        padding: 6px 10px;
        text-align: left;
    }
    .sizes-table td {
        border: 1px solid #30363d;
        padding: 6px 10px;
        color: #e6edf3;
    }

    .inventory-grid-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 0.82rem;
        text-align: center;
    }
    .inventory-grid-table th {
        background-color: rgba(22, 27, 34, 0.95);
        color: #8b949e;
        border: 1px solid #30363d;
        padding: 4px 6px;
        font-weight: 600;
    }
    .inventory-grid-table td {
        border: 1px solid #30363d;
        padding: 6px 4px;
        color: #3fb950;
        background-color: rgba(15, 20, 28, 0.6);
        font-family: monospace;
        font-weight: bold;
        font-size: 0.9rem;
    }

    @media (min-width: 992px) {
        [data-testid="stImage"] img {
            max-height: 380px !important;
            object-fit: contain !important;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 0.5rem 0.5rem 2rem 0.5rem !important;
        }
        [data-testid="stImage"] img {
            max-height: 210px !important;
            object-fit: contain !important;
        }
        div[data-testid="stRadio"] > div {
            padding: 6px 8px;
        }
    }
    </style>
""", unsafe_allow_html=True)

ancho_pantalla = streamlit_js_eval(js_expressions='window.innerWidth', key='viewport_width')
es_movil = (ancho_pantalla < 768) if ancho_pantalla is not None else False

# ==============================================================================
# CONEXIÓN SUPABASE Y DATOS BASE
# ==============================================================================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

roles_disponibles = [
    "Administrador", "Recepción", "Diseñador", "Almacén", 
    "Producción - Bordados", "Producción - Impresión", "Producción - Transferencia Térmica"
]

lista_estados = [
    "Pendiente", "Recepción", "Diseño Gráfico", "Digitalización de Bordados",
    "Producción - Bordados", "Producción - Impresión", 
    "Producción - Transferencia Térmica", "Orden Detenida", "Orden Cancelada", "Orden Entregada"
]

tallas_disponibles = ["2", "4", "6", "8", "10", "12", "14", "16", "S", "M", "WS", "WM", "L", "XL", "2XL", "3XL"]

FORMATOS_ORDEN = [
    "png", "jpg", "jpeg", "pdf", "emb", "dst", "ai", 
    "psd", "eps", "svg", "cdr", "zip", "rar", "7z", "txt", "docx"
]

def limpiar_nombre_archivo(nombre): return re.sub(r'[^a-zA-Z0-9_.-]', '_', nombre)

def subir_a_supabase(file_bytes, file_name, bucket="disenos", carpeta="almacen"):
    nombre_seguro = limpiar_nombre_archivo(file_name)
    path = f"{carpeta}/{datetime.now().strftime('%Y%m%d%H%M%S')}_{nombre_seguro}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

def obtener_siguiente_numero_orden():
    try:
        res = supabase.table("ordenes").select("nombre_orden").execute()
        if res.data:
            numeros = []
            for row in res.data:
                val = row.get("nombre_orden", "")
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
    try:
        supabase.table("ordenes").update({"estado_actual": nuevo_estado, "historial": json.dumps(lista_historial)}).eq("id", o_id).execute()
    except Exception as e:
        st.error(f"Error actualizando estado en Supabase: {e}")

def obtener_badge_estado(estado):
    colores = {
        "Pendiente": ("#e3b341", "rgba(227, 179, 65, 0.15)"),
        "Recepción": ("#58a6ff", "rgba(88, 166, 255, 0.15)"),
        "Diseño Gráfico": ("#38bdf8", "rgba(56, 189, 248, 0.15)"),
        "Digitalización de Bordados": ("#f472b6", "rgba(244, 114, 182, 0.15)"),
        "Producción - Bordados": ("#bc8cff", "rgba(188, 140, 255, 0.15)"),
        "Producción - Impresión": ("#36a3f7", "rgba(54, 163, 247, 0.15)"),
        "Producción - Transferencia Térmica": ("#f0883e", "rgba(240, 136, 62, 0.15)"),
        "Orden Detenida": ("#d29922", "rgba(210, 153, 34, 0.15)"),
        "Orden Cancelada": ("#f85149", "rgba(248, 81, 73, 0.15)"),
        "Orden Entregada": ("#3fb950", "rgba(63, 185, 80, 0.15)")
    }
    color_texto, color_bg = colores.get(estado, ("#8b949e", "rgba(139, 148, 158, 0.15)"))
    return f'<span style="background-color: {color_bg}; color: {color_texto}; border: 1px solid {color_texto}; padding: 4px 12px; border-radius: 12px; font-weight: 700; font-size: 0.85rem; display: inline-block; white-space: nowrap; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">📍 Área / Estado: {estado}</span>'

# Estado global
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})
if "colores_inventario_avanzado" not in st.session_state: st.session_state["colores_inventario_avanzado"] = {}
if "sync_trigger" not in st.session_state: st.session_state["sync_trigger"] = 0
if "nueva_orden_tallas_dinamicas" not in st.session_state: 
    st.session_state["nueva_orden_tallas_dinamicas"] = [{"talla": "S", "cantidad": 1, "comentario": ""}]

# Estados de control para el formulario de nueva orden
if "form_reset_counter" not in st.session_state: st.session_state["form_reset_counter"] = 0

count = st_autorefresh(interval=10000, key="datasync_counter")

# ==============================================================================
# ENCABEZADO Y CONTROL DE ACCESO
# ==============================================================================
col_titulo, col_header_info = st.columns([1.2, 2])

with col_titulo:
    st.title("🧵 Pixel Thread")

with col_header_info:
    if not st.session_state["autenticado"]:
        st.markdown("#### 🔐 Control de Acceso")
        col_u, col_p, col_b = st.columns([2, 2, 1])
        with col_u:
            usuario_input = st.text_input("Usuario", key="login_user_top", label_visibility="collapsed", placeholder="Usuario")
        with col_p:
            password_input = st.text_input("Contraseña", type="password", key="login_pass_top", label_visibility="collapsed", placeholder="Contraseña")
        with col_b:
            if st.button("Iniciar Sesión", key="btn_login_top", use_container_width=True):
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
                        else: st.error("❌ Credenciales incorrectas.")
                    except Exception as e: st.error(f"Error al verificar usuarios: {e}")
        st.stop()
    else:
        col_user_box, col_btn_sync, col_btn_logout = st.columns([2, 1.2, 1])
        
        with col_user_box:
            st.markdown(
                f"""
                <div class="user-card">
                    👋 <b>{st.session_state['usuario']}</b> | Rol: <i>{st.session_state['rol']}</i>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with col_btn_sync:
            if st.button("🔄 Refrescar", key="top_sync_btn", use_container_width=True):
                st.session_state["sync_trigger"] += 1
                st.rerun()
                
        with col_btn_logout:
            if st.button("🚪 Salir", key="top_logout_btn", use_container_width=True):
                st.session_state.update({"autenticado": False})
                st.rerun()

st.markdown("---")

tabs = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "📦 Almacén", "⚙️ Usuarios"])

# ==============================================================================
# TAB 1: VER ÓRDENES
# ==============================================================================
with tabs[0]:
    st.subheader("📋 Listado de Órdenes")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        busqueda = st.text_input("🔍 Buscar Cliente o # Orden", placeholder="Ej: 0000001 o Juan Perez", key="busqueda_ordenes_input")
    with col_f2:
        filtro_estado = st.selectbox("Filtrar Estado", ["Todos"] + lista_estados, key="filtro_estado_ordenes_frag")
    
    try:
        query_ordenes = supabase.table("ordenes").select("*")
        if filtro_estado != "Todos": query_ordenes = query_ordenes.eq("estado_actual", filtro_estado)
        ordenes = query_ordenes.execute().data
        
        if busqueda:
            termino = busqueda.lower()
            ordenes = [o for o in ordenes if termino in str(o.get("nombre_orden", "")).lower() or termino in o.get("nombre_cliente", "").lower()]
        
        if ordenes:
            for o in ordenes:
                o_id = o.get("id")
                numero_o = o.get('nombre_orden', 'S/N')
                cliente_o = o.get('nombre_cliente', 'Sin cliente')
                estado_actual = o.get('estado_actual', 'Pendiente')
                historial_db = o.get('historial', "[]")
                archivos_db = o.get('archivos', "[]")
                tallas_db = o.get('tallas_detalle', "[]")
                
                with st.container(border=True):
                    col_res, col_act = st.columns([2.2, 1.8])
                    with col_res: 
                        st.markdown(f"### Orden #{numero_o} - **{cliente_o}**", unsafe_allow_html=True)
                        # Etiqueta visual clara del área / estado actual
                        st.markdown(obtener_badge_estado(estado_actual), unsafe_allow_html=True)
                    
                    with col_act:
                        cols_action = st.columns([2, 1])
                        idx_actual = lista_estados.index(estado_actual) if estado_actual in lista_estados else 0
                        with cols_action[0]: 
                            nuevo_estado_sel = st.selectbox("Cambiar", lista_estados, index=idx_actual, key=f"sel_quick_{o_id}", label_visibility="collapsed")
                        with cols_action[1]:
                            if st.button("Cambiar", key=f"btn_quick_{o_id}"):
                                if nuevo_estado_sel != estado_actual:
                                    actualizar_estado_con_historial(o_id, estado_actual, nuevo_estado_sel, historial_db, st.session_state['usuario'])
                                    st.success("¡Actualizado!")
                                    st.rerun()
                    
                    # Expandidor con estado persistente guardado en st.session_state para mantenerse abierto tras recargas
                    expander_key_state = f"exp_open_{o_id}"
                    if expander_key_state not in st.session_state:
                        st.session_state[expander_key_state] = False

                    with st.expander("📂 Ver detalles completos", expanded=st.session_state[expander_key_state]):
                        st.session_state[expander_key_state] = True # Mantener abierto si el usuario interactúa
                        # Botón para activar Edición Total de la Orden
                        edit_order_mode_key = f"edit_order_full_mode_{o_id}"
                        if edit_order_mode_key not in st.session_state:
                            st.session_state[edit_order_mode_key] = False

                        if st.session_state['rol'] in ["Administrador", "Recepción"]:
                            if st.button("✏️ Editar Orden Completa", key=f"btn_toggle_edit_order_{o_id}"):
                                st.session_state[edit_order_mode_key] = not st.session_state[edit_order_mode_key]
                                st.rerun()

                        if st.session_state[edit_order_mode_key]:
                            st.info("Modo de edición completa de orden activo:")
                            with st.form(key=f"form_edit_full_order_{o_id}"):
                                edit_nombre_orden = st.text_input("Nombre / Referencia de la Orden", value=str(o.get('nombre_orden', '')))
                                edit_nombre_cliente = st.text_input("Nombre del Cliente", value=str(o.get('nombre_cliente', '')))
                                edit_telefono = st.text_input("Teléfono", value=str(o.get('telefono', '')))
                                
                                serv_actual = o.get('tipo_servicio', 'Bordado')
                                idx_serv = ["Bordado", "DTF", "Sublimación", "Mixto"].index(serv_actual) if serv_actual in ["Bordado", "DTF", "Sublimación", "Mixto"] else 0
                                edit_tipo_servicio = st.selectbox("Tipo de Servicio", ["Bordado", "DTF", "Sublimación", "Mixto"], index=idx_serv)
                                
                                try:
                                    fecha_val_parsed = datetime.strptime(str(o.get('fecha_entrega', '')), "%Y-%m-%d").date()
                                except:
                                    fecha_val_parsed = datetime.now().date()
                                edit_fecha_entrega = st.date_input("Fecha Estimada de Entrega", value=fecha_val_parsed)
                                
                                edit_total = st.number_input("TOTAL ($)", min_value=0.0, step=100.0, value=float(o.get('total', 0.0)))
                                edit_abono = st.number_input("ABONO / ANTICIPO ($)", min_value=0.0, step=100.0, value=float(o.get('abono', 0.0)))
                                edit_observaciones = st.text_area("Observaciones Generales", value=str(o.get('observaciones', '')))
                                
                                if st.form_submit_button("💾 Guardar Cambios de la Orden"):
                                    try:
                                        supabase.table("ordenes").update({
                                            "nombre_orden": edit_nombre_orden.strip(),
                                            "nombre_cliente": edit_nombre_cliente.strip(),
                                            "telefono": edit_telefono.strip(),
                                            "tipo_servicio": edit_tipo_servicio,
                                            "fecha_entrega": str(edit_fecha_entrega),
                                            "total": edit_total,
                                            "abono": edit_abono,
                                            "restante": edit_total - edit_abono,
                                            "observaciones": edit_observaciones
                                        }).eq("id", o_id).execute()
                                        
                                        st.session_state[edit_order_mode_key] = False
                                        st.success("¡Orden actualizada con éxito!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error al actualizar la orden: {err}")
                        else:
                            col_info1, col_info2 = st.columns(2)
                            with col_info1:
                                if st.session_state['rol'] in ["Administrador", "Recepción"]:
                                    st.write(f"**Teléfono:** {o.get('telefono', 'N/D')}")
                                st.write(f"**Fecha Entrega:** {o.get('fecha_entrega', 'N/D')}")
                                st.write(f"**Servicio:** {o.get('tipo_servicio', 'N/D')}")
                            with col_info2:
                                if st.session_state['rol'] in ["Administrador", "Recepción"]:
                                    st.write(f"**Total:** ${o.get('total', 0)}")
                                    st.write(f"**Abono:** ${o.get('abono', 0)}")
                                    st.write(f"**Restante:** ${o.get('restante', 0)}")
                                st.write(f"**Observaciones:** {o.get('observaciones', 'Ninguna')}")
                        
                        st.markdown("👕 **Detalle de Tallas / Sizes:**")
                        try:
                            lista_tallas = json.loads(tallas_db) if isinstance(tallas_db, str) else tallas_db
                            
                            edit_mode_key = f"edit_tallas_mode_{o_id}"
                            if edit_mode_key not in st.session_state:
                                st.session_state[edit_mode_key] = False

                            if st.session_state['rol'] in ["Administrador", "Recepción", "Producción - Bordados", "Almacén"]:
                                if st.button("✏️ Editar Tallas y Cantidades", key=f"btn_toggle_edit_tallas_{o_id}"):
                                    st.session_state[edit_mode_key] = not st.session_state[edit_mode_key]
                                    st.rerun()

                            if st.session_state[edit_mode_key]:
                                st.info("Modo de edición manual activo:")
                                with st.form(key=f"form_edit_tallas_{o_id}"):
                                    tallas_existentes_map = {item.get("talla"): item for item in (lista_tallas if isinstance(lista_tallas, list) else [])}
                                    tallas_a_editar = st.multiselect("Seleccionar Tallas", options=tallas_disponibles, default=list(tallas_existentes_map.keys()), key=f"ms_edit_{o_id}")
                                    
                                    temp_tallas_actualizadas = []
                                    for sz in tallas_a_editar:
                                        datos_previos = tallas_existentes_map.get(sz, {"cantidad": 1, "comentario": ""})
                                        c_col1, c_col2 = st.columns([1, 2])
                                        with c_col1:
                                            cant_val = st.number_input(f"Cantidad {sz}", min_value=0, value=int(datos_previos.get("cantidad", 1)), step=1, key=f"edit_cant_{o_id}_{sz}")
                                        with c_col2:
                                            obs_val = st.text_input(f"Comentario {sz}", value=str(datos_previos.get("comentario", "")), key=f"edit_obs_{o_id}_{sz}")
                                        
                                        temp_tallas_actualizadas.append({
                                            "talla": sz,
                                            "cantidad": int(cant_val),
                                            "comentario": obs_val.strip()
                                        })
                                    
                                    if st.form_submit_button("💾 Guardar Cambios de Tallas"):
                                        try:
                                            supabase.table("ordenes").update({"tallas_detalle": json.dumps(temp_tallas_actualizadas)}).eq("id", o_id).execute()
                                            st.session_state[edit_mode_key] = False
                                            st.success("¡Tallas actualizadas correctamente!")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error al actualizar tallas: {err}")
                            else:
                                if lista_tallas and len(lista_tallas) > 0:
                                    rows_html = ""
                                    total_piezas = 0
                                    for item_t in lista_tallas:
                                        sz = item_t.get("talla", "-")
                                        cant = item_t.get("cantidad", 0)
                                        obs = item_t.get("comentario", "-") or "-"
                                        total_piezas += cant
                                        rows_html += f"<tr><td><b>{sz}</b></td><td>{cant}</td><td>{obs}</td></tr>"
                                    
                                    table_html = f"""
                                    <table class="sizes-table">
                                        <thead>
                                            <tr>
                                                <th>Talla / Size</th>
                                                <th>Cantidad</th>
                                                <th>Comentario / Detalle</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {rows_html}
                                            <tr style="background-color: rgba(255,255,255,0.05); font-weight: bold;">
                                                <td>TOTAL PIEZAS</td>
                                                <td>{total_piezas}</td>
                                                <td>-</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    """
                                    st.markdown(table_html, unsafe_allow_html=True)
                                else:
                                    st.caption("No hay desglose de tallas registrado.")
                        except Exception as err:
                            st.caption(f"No se pudo procesar la información de tallas: {err}")

                        st.markdown("---")
                        st.markdown("📎 **Archivos Adjuntos:**")
                        
                        try:
                            lista_archivos = json.loads(archivos_db) if isinstance(archivos_db, str) else archivos_db
                            if not isinstance(lista_archivos, list):
                                lista_archivos = []
                        except:
                            lista_archivos = []

                        if lista_archivos:
                            for idx_arch, item_file in enumerate(lista_archivos):
                                url_f = item_file.get("url", "") if isinstance(item_file, dict) else item_file
                                nom_f = item_file.get("nombre", f"Archivo {idx_arch+1}") if isinstance(item_file, dict) else f"Archivo {idx_arch+1}"
                                
                                col_f_view, col_f_del = st.columns([5, 1])
                                with col_f_view:
                                    ext_archivo = nom_f.lower().split('.')[-1] if '.' in nom_f else ""
                                    if ext_archivo in ["png", "jpg", "jpeg", "webp", "gif"]:
                                        col_thumb, col_link = st.columns([1, 4])
                                        with col_thumb:
                                            st.image(url_f, width=70)
                                        with col_link:
                                            st.markdown(f"📄 [{nom_f}]({url_f})")
                                    else:
                                        st.markdown(f"- 📄 [{nom_f}]({url_f})")
                                with col_f_del:
                                    if st.button("🗑️", key=f"del_file_{o_id}_{idx_arch}", help=f"Eliminar {nom_f}"):
                                        lista_archivos.pop(idx_arch)
                                        try:
                                            supabase.table("ordenes").update({"archivos": json.dumps(lista_archivos)}).eq("id", o_id).execute()
                                            st.success(f"Archivo '{nom_f}' eliminado.")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error al eliminar archivo: {err}")
                        else:
                            st.caption("No se adjuntaron archivos en esta orden.")

                        st.markdown("")
                        nuevos_archivos_extras = st.file_uploader(
                            "➕ Agregar más archivos a esta orden", 
                            type=FORMATOS_ORDEN, 
                            accept_multiple_files=True,
                            key=f"uploader_add_more_{o_id}"
                        )
                        if nuevos_archivos_extras:
                            if st.button("💾 Subir y Guardar Nuevos Archivos", key=f"btn_save_extras_{o_id}"):
                                with st.spinner("Subiendo archivos adicionales..."):
                                    try:
                                        for arch in nuevos_archivos_extras:
                                            url_file = subir_a_supabase(arch.getvalue(), arch.name, bucket="disenos", carpeta="ordenes_archivos")
                                            lista_archivos.append({"nombre": arch.name, "url": url_file})
                                        
                                        supabase.table("ordenes").update({"archivos": json.dumps(lista_archivos)}).eq("id", o_id).execute()
                                        st.success("¡Archivos agregados exitosamente!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error al subir los archivos: {err}")

                        st.markdown("---")
                        st.markdown("📜 **Historial:**")
                        try:
                            registros = json.loads(historial_db) if isinstance(historial_db, str) else historial_db
                            if registros:
                                for reg in registros[:5]:
                                    st.caption(f"🕒 {reg.get('fecha', '-')} | 👤 {reg.get('usuario', '-')}: {reg.get('de', '')} ➡️ {reg.get('a', '')}")
                        except: st.caption("Sin historial.")

                        if st.session_state['rol'] == "Administrador":
                            st.markdown("---")
                            confirm_key = f"confirm_del_orden_{o_id}"
                            
                            if not st.session_state.get(confirm_key, False):
                                if st.button(f"🗑️ Eliminar Orden #{numero_o}", key=f"btn_init_del_orden_{o_id}"):
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                            else:
                                st.warning(f"⚠️ ¿Seguro que deseas eliminar permanentemente la Orden #{numero_o}?")
                                col_del_yes, col_del_no = st.columns(2)
                                with col_del_yes:
                                    if st.button("✅ Sí, Eliminar", key=f"btn_confirm_del_yes_{o_id}"):
                                        try:
                                            supabase.table("ordenes").delete().eq("id", o_id).execute()
                                            st.session_state[confirm_key] = False
                                            st.success(f"Orden #{numero_o} eliminada exitosamente.")
                                            st.rerun()
                                        except Exception as err:
                                            st.error(f"Error al eliminar la orden: {err}")
                                with col_del_no:
                                    if st.button("❌ Cancelar", key=f"btn_confirm_del_no_{o_id}"):
                                        st.session_state[confirm_key] = False
                                        st.rerun()

        else: st.info("No hay órdenes encontradas.")
    except Exception as e: st.error(f"Error al cargar órdenes de Supabase: {e}")

# ==============================================================================
# TAB 2: NUEVA ORDEN
# ==============================================================================
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    
    rc = st.session_state["form_reset_counter"]
    numero_auto = obtener_siguiente_numero_orden()
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        nombre_orden_input = st.text_input("Nombre / Referencia de la Orden", value=numero_auto, key=f"input_nombre_orden_{rc}")
        nombre_cliente = st.text_input("Nombre del Cliente", key=f"input_cliente_{rc}")
        telefono_cliente = st.text_input("Teléfono", key=f"input_telefono_{rc}")
    with col_c2:
        tipo_servicio = st.selectbox("Tipo de Servicio", ["Bordado", "DTF", "Sublimación", "Mixto"], key=f"sel_servicio_{rc}")
        fecha_entrega = st.date_input("Fecha Estimada de Entrega", key=f"date_entrega_{rc}")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        total_orden = st.number_input("TOTAL ($)", min_value=0.0, step=100.0, key=f"num_total_{rc}")
    with col_m2:
        abono_orden = st.number_input("ABONO / ANTICIPO ($)", min_value=0.0, step=100.0, key=f"num_abono_{rc}")
    
    st.markdown("---")
    archivos_subidos = st.file_uploader(
        "📁 Adjuntar Archivos (Múltiples formatos: PNG, JPG, PDF, EMB, DST, AI, PSD, ZIP, etc.)", 
        type=FORMATOS_ORDEN, 
        accept_multiple_files=True,
        key=f"uploader_archivos_orden_{rc}"
    )
    
    observaciones = st.text_area("Observaciones Generales", key=f"area_obs_{rc}")
    
    st.markdown("---")
    st.markdown("👕 **Selección e Información de Tallas / Sizes**")
    col_add_btn, col_clear_btn = st.columns([2, 1])
    with col_add_btn:
        if st.button("➕ Agregar Talla", key="btn_add_talla_fila"):
            st.session_state["nueva_orden_tallas_dinamicas"].append({"talla": "S", "cantidad": 1, "comentario": ""})
            st.rerun()
    with col_clear_btn:
        if st.button("🗑️ Limpiar Tallas", key="btn_clear_tallas_fila"):
            st.session_state["nueva_orden_tallas_dinamicas"] = []
            st.rerun()

    dict_detalle_tallas = []
    if st.session_state["nueva_orden_tallas_dinamicas"]:
        for idx, item_talla in enumerate(st.session_state["nueva_orden_tallas_dinamicas"]):
            cols_fila = st.columns([1.5, 1, 2.5, 0.5])
            with cols_fila[0]:
                talla_sel = st.selectbox(f"Talla #{idx+1}", options=tallas_disponibles, index=tallas_disponibles.index(item_talla["talla"]) if item_talla["talla"] in tallas_disponibles else 0, key=f"dinamica_talla_{idx}_{rc}")
            with cols_fila[1]:
                cant_val = st.number_input(f"Cant #{idx+1}", min_value=1, value=int(item_talla["cantidad"]), step=1, key=f"dinamica_cant_{idx}_{rc}")
            with cols_fila[2]:
                obs_val = st.text_input(f"Detalle #{idx+1}", value=item_talla["comentario"], placeholder="Ej: Nombre Juan #10...", key=f"dinamica_obs_{idx}_{rc}")
            with cols_fila[3]:
                st.write("") 
                st.write("")
                if st.button("❌", key=f"dinamica_del_{idx}_{rc}"):
                    st.session_state["nueva_orden_tallas_dinamicas"].pop(idx)
                    st.rerun()
            
            dict_detalle_tallas.append({
                "talla": talla_sel,
                "cantidad": int(cant_val),
                "comentario": obs_val.strip()
            })
    else:
        st.info("Haz clic en '➕ Agregar Talla' para añadir tallas a esta orden.")

    st.markdown("---")
    if st.button("💾 Guardar Orden", use_container_width=True):
        if not nombre_orden_input.strip():
            st.error("⚠️ Debes ingresar el nombre o número de la orden.")
        elif not dict_detalle_tallas:
            st.error("⚠️ Debes agregar al menos una talla a la orden.")
        else:
            try:
                urls_archivos = []
                if archivos_subidos:
                    with st.spinner("Subiendo archivos..."):
                        for arch in archivos_subidos:
                            url_file = subir_a_supabase(arch.getvalue(), arch.name, bucket="disenos", carpeta="ordenes_archivos")
                            urls_archivos.append({"nombre": arch.name, "url": url_file})

                historial_inicial = json.dumps([{
                    "usuario": st.session_state['usuario'], 
                    "de": "Inicio", 
                    "a": "Pendiente", 
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                
                supabase.table("ordenes").insert({
                    "nombre_orden": nombre_orden_input.strip(),
                    "nombre_cliente": nombre_cliente,
                    "telefono": telefono_cliente,
                    "tipo_servicio": tipo_servicio,
                    "fecha_entrega": str(fecha_entrega),
                    "total": total_orden,
                    "abono": abono_orden,
                    "restante": total_orden - abono_orden,
                    "observaciones": observaciones,
                    "tallas_detalle": json.dumps(dict_detalle_tallas),
                    "archivos": json.dumps(urls_archivos),
                    "estado_actual": "Pendiente",
                    "historial": historial_inicial
                }).execute()
                
                st.session_state["nueva_orden_tallas_dinamicas"] = [{"talla": "S", "cantidad": 1, "comentario": ""}]
                st.session_state["form_reset_counter"] += 1
                st.success("✅ ¡La orden se guardó correctamente y el formulario ha quedado limpio!")
                time.sleep(1)
                st.rerun()
            except Exception as err:
                st.error(f"❌ Error al guardar la orden en Supabase: {err}")

# ==============================================================================
# TAB 3: ALMACÉN
# ==============================================================================
with tabs[2]:
    st.subheader("📦 Control de Inventario")
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Producto", expanded=False):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA", key="input_nombre_prenda_color_img")
            st.markdown("---")
            st.markdown("🎨 **Añadir Color e Imagen**")
            
            col_picker, col_text = st.columns([1, 2])
            with col_picker:
                color_picker_val = st.color_picker("Tono", "#3b82f6", key="picker_color_hex_v2")
            with col_text:
                nuevo_color = st.text_input("NOMBRE DEL COLOR", value=color_picker_val, key="input_nuevo_color_nombre_v2")
            
            foto_color = st.file_uploader(f"🖼️ Imagen para `{nuevo_color}`", type=["png", "jpg", "jpeg"], key=f"uploader_img_{nuevo_color}")
            
            if st.button("➕ Añadir Color"):
                if nuevo_color.strip():
                    c_clean = nuevo_color.strip()
                    if c_clean not in st.session_state["colores_inventario_avanzado"]:
                        st.session_state["colores_inventario_avanzado"][c_clean] = {
                            "tallas": {t: 0 for t in tallas_disponibles},
                            "imagen_file": foto_color,
                            "hex": color_picker_val if color_picker_val.startswith("#") else "#3b82f6"
                        }
                        st.success(f"Color '{c_clean}' agregado.")
                        st.rerun()
                    else:
                        st.warning("El color ya existe.")
                else:
                    st.error("Ingresa un nombre de color válido.")

            if st.session_state["colores_inventario_avanzado"]:
                st.markdown("#### 🔍 Existencias por Color:")
                color_activo = st.selectbox("Color a configurar:", list(st.session_state["colores_inventario_avanzado"].keys()), key="select_color_activo_v2")
                
                if color_activo:
                    st.markdown(f"📏 **Tallas para `{color_activo}`**")
                    cols_grid = st.columns(2 if es_movil else 5)
                    num_cols = len(cols_grid)
                    for idx, talla in enumerate(tallas_disponibles):
                        col_actual = cols_grid[idx % num_cols]
                        with col_actual:
                            val_actual = st.session_state["colores_inventario_avanzado"][color_activo]["tallas"].get(talla, 0)
                            nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=int(val_actual), key=f"cant_v2_{color_activo}_{talla}")
                            st.session_state["colores_inventario_avanzado"][color_activo]["tallas"][talla] = int(nueva_cant)
                            
                    if st.button("🗑️ Eliminar color", key=f"del_col_v2_{color_activo}"):
                        del st.session_state["colores_inventario_avanzado"][color_activo]
                        st.rerun()

            st.markdown("---")
            if st.button("💾 Guardar Inventario Completo"):
                if not inv_nombre.strip():
                    st.error("⚠️ Debes ingresar el nombre del producto.")
                elif not st.session_state["colores_inventario_avanzado"]:
                    st.error("⚠️ Agrega al menos un color con sus tallas.")
                else:
                    try:
                        data_a_guardar = {}
                        primera_imagen_url = ""
                        for col_key, col_data in st.session_state["colores_inventario_avanzado"].items():
                            img_file = col_data["imagen_file"]
                            img_url = ""
                            if img_file is not None:
                                img_url = subir_a_supabase(img_file.getvalue(), img_file.name)
                                if not primera_imagen_url:
                                    primera_imagen_url = img_url
                            
                            data_a_guardar[col_key] = {
                                "tallas": col_data["tallas"],
                                "imagen_url": img_url,
                                "hex": col_data.get("hex", "#3b82f6")
                            }
                        
                        supabase.table("almacen").insert({
                            "nombre_producto": inv_nombre.strip(),
                            "imagen_url": primera_imagen_url,
                            "tallas_existencias": json.dumps(data_a_guardar)
                        }).execute()
                        
                        st.success("¡Inventario guardado con éxito!")
                        st.session_state["colores_inventario_avanzado"] = {}
                        st.rerun()
                    except Exception as err:
                        st.error(f"❌ Error al guardar inventario en Supabase: {err}")

    st.markdown("---")
    st.subheader("📦 Productos en Inventario")
    try:
        res_inv = supabase.table("almacen").select("*").execute()
        if res_inv.data:
            for prod in res_inv.data:
                p_id = prod.get("id")
                p_nombre = prod.get("nombre_producto", "Sin Nombre")
                p_tallas_raw = prod.get("tallas_existencias", "{}")
                
                try:
                    p_datos = json.loads(p_tallas_raw) if isinstance(p_tallas_raw, str) else p_tallas_raw
                except: p_datos = {}

                with st.container(border=True):
                    col_p_info, col_p_img = st.columns([3, 1])
                    with col_p_info:
                        st.markdown(f"### {p_nombre}")
                        
                        # Opción de edición total del producto en inventario
                        edit_prod_mode_key = f"edit_prod_mode_{p_id}"
                        if edit_prod_mode_key not in st.session_state:
                            st.session_state[edit_prod_mode_key] = False

                        if puede_modificar:
                            if st.button("✏️ Editar Producto Completo", key=f"btn_toggle_edit_prod_{p_id}"):
                                st.session_state[edit_prod_mode_key] = not st.session_state[edit_prod_mode_key]
                                st.rerun()

                        if st.session_state[edit_prod_mode_key]:
                            st.info("Modo de edición de producto activo:")
                            with st.form(key=f"form_edit_prod_{p_id}"):
                                edit_p_nombre = st.text_input("Nombre del Producto", value=str(p_nombre))
                                
                                st.markdown("#### Editar Existencias por Color y Tallas:")
                                temp_edit_datos = {}
                                
                                colores_keys_actuales = list(p_datos.keys()) if isinstance(p_datos, dict) else []
                                
                                for c_k in colores_keys_actuales:
                                    st.markdown(f"🔹 **Color: {c_k}**")
                                    tallas_actuales_color = p_datos[c_k].get("tallas", {})
                                    img_url_actual = p_datos[c_k].get("imagen_url", "")
                                    hex_actual = p_datos[c_k].get("hex", "#3b82f6")
                                    
                                    cols_t_edit = st.columns(4)
                                    nuevas_tallas_col = {}
                                    for idx_t, t_s in enumerate(tallas_disponibles):
                                        val_t_prev = tallas_actuales_color.get(t_s, 0)
                                        with cols_t_edit[idx_t % 4]:
                                            nuevas_tallas_col[t_s] = st.number_input(f"Talla {t_s} ({c_k})", min_value=0, step=1, value=int(val_t_prev), key=f"edit_inv_t_{p_id}_{c_k}_{t_s}")
                                    
                                    temp_edit_datos[c_k] = {
                                        "tallas": nuevas_tallas_col,
                                        "imagen_url": img_url_actual,
                                        "hex": hex_actual
                                    }

                                if st.form_submit_button("💾 Guardar Cambios del Producto"):
                                    try:
                                        supabase.table("almacen").update({
                                            "nombre_producto": edit_p_nombre.strip(),
                                            "tallas_existencias": json.dumps(temp_edit_datos)
                                        }).eq("id", p_id).execute()
                                        
                                        st.session_state[edit_prod_mode_key] = False
                                        st.success("¡Producto actualizado exitosamente!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error al actualizar producto: {err}")
                        else:
                            if p_datos:
                                colores_disponibles_list = list(p_datos.keys())
                                color_seleccionado_ver = st.selectbox("Color", colores_disponibles_list, key=f"sel_ver_color_{p_id}")
                                
                                if color_seleccionado_ver in p_datos:
                                    info_color = p_datos[color_seleccionado_ver]
                                    tallas_dict = info_color.get("tallas", {})
                                    
                                    filas_grid = f"""
                                    <table class="inventory-grid-table">
                                        <tr>
                                            {''.join([f"<th>{t}</th>" for t in tallas_disponibles[:8]])}
                                        </tr>
                                        <tr>
                                            {''.join([f"<td>{tallas_dict.get(t, 0)}</td>" for t in tallas_disponibles[:8]])}
                                        </tr>
                                        <tr>
                                            {''.join([f"<th>{t}</th>" for t in tallas_disponibles[8:]])}
                                        </tr>
                                        <tr>
                                            {''.join([f"<td>{tallas_dict.get(t, 0)}</td>" for t in tallas_disponibles[8:]])}
                                        </tr>
                                    </table>
                                    """
                                    st.markdown(filas_grid, unsafe_allow_html=True)
                                    
                                    img_url_color = info_color.get("imagen_url", "") or prod.get("imagen_url", "")
                                    with col_p_img:
                                        if img_url_color:
                                            st.image(img_url_color, use_container_width=True)
                                        else:
                                            st.caption("Sin imagen")
                    
                    if puede_modificar:
                        if st.button(f"🗑️ Eliminar Producto", key=f"del_prod_{p_id}"):
                            try:
                                supabase.table("almacen").delete().eq("id", p_id).execute()
                                st.success("Producto eliminado.")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error al eliminar producto: {ex}")
        else:
            st.caption("No hay productos registrados en el almacén.")
    except Exception as e:
        st.error(f"❌ Error al consultar la tabla 'almacen' em Supabase: {e}")

# ==============================================================================
# TAB 4: USUARIOS
# ==============================================================================
with tabs[3]:
    st.subheader("⚙️ Gestión de Usuarios")
    if st.session_state['rol'] == "Administrador":
        with st.form("form_crear_usuario"):
            u_nombre = st.text_input("Nombre de Usuario")
            u_pass = st.text_input("Contraseña", type="password")
            u_rol = st.selectbox("Rol del Usuario", roles_disponibles)
            
            if st.form_submit_button("➕ Registrar Usuario"):
                if u_nombre.strip() and u_pass.strip():
                    try:
                        supabase.table("usuarios").insert({
                            "usuario": u_nombre.strip(),
                            "password": u_pass.strip(),
                            "rol_id": u_rol
                        }).execute()
                        st.success(f"Usuario '{u_nombre}' creado con éxito.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"❌ Error al registrar usuario en Supabase: {err}")
                else:
                    st.warning("Completa todos los campos.")
        
        st.markdown("---")
        st.markdown("### 📋 Usuarios Registrados")
        try:
            res_u = supabase.table("usuarios").select("*").execute()
            if res_u.data:
                for usr in res_u.data:
                    u_id = usr.get("id")
                    u_n = usr.get("usuario")
                    u_p = usr.get("password")
                    u_r = usr.get("rol_id")
                    
                    with st.container(border=True):
                        col_u1, col_u2 = st.columns([3, 1])
                        with col_u1:
                            st.write(f"👤 **{u_n}** — Rol: *{u_r}*")
                        with col_u2:
                            if u_n.lower() != "admin":
                                if st.button("🗑️ Eliminar", key=f"del_user_{u_id}"):
                                    try:
                                        supabase.table("usuarios").delete().eq("id", u_id).execute()
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error al eliminar usuario: {err}")

                        # Botón para editar usuario de manera total
                        edit_user_mode_key = f"edit_user_mode_{u_id}"
                        if edit_user_mode_key not in st.session_state:
                            st.session_state[edit_user_mode_key] = False

                        if st.button("✏️ Editar Usuario", key=f"btn_toggle_edit_user_{u_id}"):
                            st.session_state[edit_user_mode_key] = not st.session_state[edit_user_mode_key]
                            st.rerun()

                        if st.session_state[edit_user_mode_key]:
                            with st.form(key=f"form_edit_user_{u_id}"):
                                edit_u_nombre = st.text_input("Nombre de Usuario", value=str(u_n))
                                edit_u_pass = st.text_input("Contraseña", value=str(u_p), type="password")
                                
                                idx_rol = roles_disponibles.index(u_r) if u_r in roles_disponibles else 0
                                edit_u_rol = st.selectbox("Rol del Usuario", roles_disponibles, index=idx_rol)
                                
                                if st.form_submit_button("💾 Guardar Cambios de Usuario"):
                                    try:
                                        supabase.table("usuarios").update({
                                            "usuario": edit_u_nombre.strip(),
                                            "password": edit_u_pass.strip(),
                                            "rol_id": edit_u_rol
                                        }).eq("id", u_id).execute()
                                        
                                        st.session_state[edit_user_mode_key] = False
                                        st.success("¡Usuario actualizado correctamente!")
                                        st.rerun()
                                    except Exception as err:
                                        st.error(f"Error al actualizar usuario: {err}")
            else:
                st.caption("No hay usuarios adicionales registrados.")
        except Exception as e:
            st.error(f"❌ Error al consultar la tabla 'usuarios' en Supabase: {e}")
    else:
        st.warning("⚠️ No tienes permisos de Administrador para ver esta sección.")
