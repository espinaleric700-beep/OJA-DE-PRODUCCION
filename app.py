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
# CONFIGURACIÓN Y ESTILOS CSS ADAPTATIVOS (PC VS MÓVIL)
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
    /* Estilos Generales Dark Theme con Patrón de Rejilla/Lienzo */
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

    /* Imagen general con fondo transparente */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        align-items: center;
        background: transparent !important;
        border-radius: 0px !important;
        padding: 0px !important;
        box-shadow: none !important;
    }

    /* Estilos de inputs de Tallas */
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

    /* Selector de color */
    div[data-testid="stRadio"] > div {
        gap: 8px !important;
        flex-wrap: wrap !important;
        background: rgba(22, 27, 34, 0.85);
        padding: 8px 12px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }

    /* Estilo para las tarjetas de las órdenes */
    div[data-testid="stVerticalBlock"] > div:has(div.order-card-marker) {
        background-color: rgba(22, 27, 34, 0.75);
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* MEDIA QUERIES: PC VS MÓVIL */
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

# Detectar ancho de la pantalla dinámicamente
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

def obtener_badge_estado(estado):
    colores = {
        "Pendiente": ("#e3b341", "rgba(227, 179, 65, 0.15)"),
        "Recepción": ("#58a6ff", "rgba(88, 166, 255, 0.15)"),
        "Producción - Bordados": ("#bc8cff", "rgba(188, 140, 255, 0.15)"),
        "Producción - Impresión": ("#36a3f7", "rgba(54, 163, 247, 0.15)"),
        "Producción - Transferencia Térmica": ("#f0883e", "rgba(240, 136, 62, 0.15)"),
        "Orden Detenida": ("#d29922", "rgba(210, 153, 34, 0.15)"),
        "Orden Cancelada": ("#f85149", "rgba(248, 81, 73, 0.15)"),
        "Orden Entregada": ("#3fb950", "rgba(63, 185, 80, 0.15)")
    }
    color_texto, color_bg = colores.get(estado, ("#8b949e", "rgba(139, 148, 158, 0.15)"))
    return f"""<span style="
        background-color: {color_bg};
        color: {color_texto};
        border: 1px solid {color_texto};
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
        white-space: nowrap;
    ">{estado}</span>"""

# Estado global
if "autenticado" not in st.session_state: st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})
if "colores_inventario_avanzado" not in st.session_state: st.session_state["colores_inventario_avanzado"] = {}
if "sync_trigger" not in st.session_state: st.session_state["sync_trigger"] = 0

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
                    except Exception as e: st.error(f"Error: {e}")
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
# TAB 1: VER ÓRDENES (TARJETAS VISUALMENTE SEPARADAS)
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
        if filtro_estado != "Todos": query_ordenes = query_ordenes.eq("estado", filtro_estado)
        ordenes = query_ordenes.execute().data
        
        if busqueda:
            termino = busqueda.lower()
            ordenes = [o for o in ordenes if termino in str(o.get("numero_orden", "")).lower() or termino in o.get("nombre_cliente", "").lower()]
        
        if ordenes:
            for o in ordenes:
                o_id = o.get("id")
                numero_o = o.get('numero_orden', 'S/N')
                cliente_o = o.get('nombre_cliente', 'Sin cliente')
                estado_actual = o.get('estado', 'Pendiente')
                historial_db = o.get('historial', "[]")
                
                # Tarjeta contenedora de la orden
                with st.container():
                    st.markdown('<div class="order-card-marker"></div>', unsafe_allow_html=True)
                    col_res, col_act = st.columns([2.2, 1.8])
                    with col_res: 
                        badge_html = obtener_badge_estado(estado_actual)
                        st.markdown(f"### Orden #{numero_o} - **{cliente_o}** {badge_html}", unsafe_allow_html=True)
                    
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
                    
                    with st.expander("📂 Ver detalles completos"):
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
                        st.markdown("---")
                        st.markdown("📜 **Historial:**")
                        try:
                            registros = json.loads(historial_db) if isinstance(historial_db, str) else historial_db
                            if registros:
                                for reg in registros[:5]:
                                    st.caption(f"🕒 {reg.get('fecha', '-')} | 👤 {reg.get('usuario', '-')}: {reg.get('de', '')} ➡️ {reg.get('a', '')}")
                        except: st.caption("Sin historial.")
                
                st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        else: st.info("No hay órdenes encontradas.")
    except Exception as e: st.error(f"Error: {e}")

# ==============================================================================
# TAB 2: NUEVA ORDEN
# ==============================================================================
with tabs[1]:
    st.subheader("➕ Crear Nueva Orden")
    numero_auto = obtener_siguiente_numero_orden()
    with st.form("form_crear_orden_completa"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.text_input("Número de Orden (Auto)", value=numero_auto, disabled=True)
            nombre_cliente = st.text_input("Nombre del Cliente")
            telefono_cliente = st.text_input("Teléfono")
        with col_c2:
            tipo_servicio = st.selectbox("Tipo de Servicio", ["Bordado", "DTF", "Sublimación", "Mixto"])
            fecha_entrega = st.date_input("Fecha Estimada de Entrega")
        total_orden = st.number_input("Total ($)", min_value=0.0, step=100.0)
        abono_orden = st.number_input("Abono / Anticipo ($)", min_value=0.0, step=100.0)
        observaciones = st.text_area("Observaciones")
        if st.form_submit_button("💾 Guardar Orden"):
            historial_inicial = json.dumps([{
                "usuario": st.session_state['usuario'], 
                "de": "Inicio", 
                "a": "Pendiente", 
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            supabase.table("ordenes").insert({
                "numero_orden": numero_auto, "nombre_cliente": nombre_cliente, "telefono": telefono_cliente,
                "tipo_servicio": tipo_servicio, "fecha_entrega": str(fecha_entrega), "total": total_orden,
                "abono": abono_orden, "restante": total_orden - abono_orden, "observaciones": observaciones,
                "estado": "Pendiente", "historial": historial_inicial
            }).execute()
            st.success("¡Orden creada!")
            st.rerun()

# ==============================================================================
# TAB 3: ALMACÉN (DIFERENCIADO PC VS MÓVIL)
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
                        st.success("✅ ¡Producto guardado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
        st.divider()

    @st.fragment
    def render_inventario_fresco(trigger_val):
        try:
            response = supabase.table("almacen").select("*").execute()
            inventario_db = response.data
            
            if inventario_db:
                st.markdown("### 📋 Existencias Actuales")
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
                                else:
                                    dict_colores = temp_data
                    except Exception:
                        dict_colores = {}

                    st.markdown(f"#### 🏷️ {p_nombre}")
                    
                    if dict_colores:
                        lista_cols = list(dict_colores.keys())
                        
                        color_sel = st.radio(
                            "Selecciona Color:",
                            options=lista_cols,
                            key=f"radio_color_{item_id}_{trigger_val}",
                            horizontal=True
                        )
                        
                        data_color = dict_colores.get(color_sel, {})
                        
                        if es_movil:
                            if data_color.get("imagen_url"): 
                                st.image(data_color["imagen_url"], use_container_width=True)
                            else:
                                st.caption("📷 Sin imagen disponible")
                            
                            st.markdown(f"**Tallas Disponibles (`{color_sel}`):**")
                            tallas_del_color = data_color.get("tallas", {})
                            
                            cols_tallas_grid = st.columns(2)
                            for idx, talla in enumerate(tallas_disponibles):
                                target_col = cols_tallas_grid[idx % 2]
                                with target_col:
                                    cantidad = int(tallas_del_color.get(talla, 0))
                                    if puede_modificar:
                                        nueva_cant = st.number_input(
                                            f"Talla {talla}", 
                                            min_value=0, 
                                            step=1, 
                                            value=cantidad, 
                                            key=f"num_{item_id}_{color_sel}_{talla}_{trigger_val}"
                                        )
                                        if nueva_cant != cantidad:
                                            dict_colores[color_sel]["tallas"][talla] = int(nueva_cant)
                                            supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                    else:
                                        st.markdown(f"**Talla {talla}:** `{cantidad:02d}`")
                        else:
                            col_img, col_info = st.columns([1, 2], gap="large")
                            
                            with col_img:
                                if data_color.get("imagen_url"): 
                                    st.image(data_color["imagen_url"], use_container_width=True)
                                else:
                                    st.caption("📷 Sin imagen disponible")
                                    
                            with col_info:
                                st.markdown(f"**Tallas Disponibles (`{color_sel}`):**")
                                tallas_del_color = data_color.get("tallas", {})
                                
                                cols_tallas_grid = st.columns(5)
                                for idx, talla in enumerate(tallas_disponibles):
                                    target_col = cols_tallas_grid[idx % 5]
                                    with target_col:
                                        cantidad = int(tallas_del_color.get(talla, 0))
                                        if puede_modificar:
                                            nueva_cant = st.number_input(
                                                f"Talla {talla}", 
                                                min_value=0, 
                                                step=1, 
                                                value=cantidad, 
                                                key=f"num_{item_id}_{color_sel}_{talla}_{trigger_val}"
                                            )
                                            if nueva_cant != cantidad:
                                                dict_colores[color_sel]["tallas"][talla] = int(nueva_cant)
                                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                        else:
                                            st.markdown(f"**Talla {talla}:** `{cantidad:02d}`")

                    if puede_modificar:
                        with st.expander(f"⚙️ Ajustes de {p_nombre}"):
                            nueva_img_file = st.file_uploader(f"Nueva imagen ({color_sel})", type=["png", "jpg", "jpeg"], key=f"up_img_{item_id}_{color_sel}_{trigger_val}")
                            if st.button("💾 Actualizar Imagen", key=f"btn_img_{item_id}_{color_sel}_{trigger_val}"):
                                if nueva_img_file:
                                    url_subida = subir_a_supabase(nueva_img_file.getvalue(), nueva_img_file.name)
                                    dict_colores[color_sel]["imagen_url"] = url_subida
                                    supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                    st.success("¡Imagen actualizada!")
                                    st.rerun()
                                    
                            if st.button("🗑️ Eliminar Producto", key=f"del_prod_{item_id}_{trigger_val}"):
                                supabase.table("almacen").delete().eq("id", item_id).execute()
                                st.rerun()
                    st.divider()
            else:
                st.info("No hay productos en almacén.")
        except Exception as e:
            st.error(f"Error al cargar inventario: {e}")

    render_inventario_fresco(st.session_state["sync_trigger"])

# ==============================================================================
# TAB 4: USUARIOS
# ==============================================================================
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
                        st.success("✅ Usuario creado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Completa los campos.")
        
        st.markdown("---")
        st.subheader("Usuarios Registrados")
        try:
            usuarios_db = supabase.table("usuarios").select("*").execute().data
            if usuarios_db:
                for u in usuarios_db:
                    u_id = u.get('id')
                    u_nombre = u.get('usuario')
                    u_pass = u.get('password')
                    u_rol = u.get('rol_id')

                    col_u1, col_u2, col_u3 = st.columns([2, 1, 1])
                    with col_u1:
                        st.markdown(f"👤 **{u_nombre}** ({u_rol})")
                    with col_u2:
                        btn_editar = st.button("✏️ Modificar", key=f"btn_edit_user_{u_id}")
                    with col_u3:
                        if st.button("🗑️ Eliminar", key=f"del_user_{u_id}"):
                            supabase.table("usuarios").delete().eq("id", u_id).execute()
                            st.success("Eliminado")
                            st.rerun()

                    if f"edit_mode_{u_id}" not in st.session_state:
                        st.session_state[f"edit_mode_{u_id}"] = False

                    if btn_editar:
                        st.session_state[f"edit_mode_{u_id}"] = not st.session_state[f"edit_mode_{u_id}"]
                        st.rerun()

                    if st.session_state.get(f"edit_mode_{u_id}", False):
                        with st.form(key=f"form_mod_user_{u_id}"):
                            st.markdown(f"**Editar: {u_nombre}**")
                            mod_nombre = st.text_input("Usuario", value=u_nombre, key=f"mod_n_{u_id}")
                            mod_pass = st.text_input("Contraseña", value=u_pass, type="password", key=f"mod_p_{u_id}")
                            
                            idx_rol_actual = roles_disponibles.index(u_rol) if u_rol in roles_disponibles else 0
                            mod_rol = st.selectbox("Rol", roles_disponibles, index=idx_rol_actual, key=f"mod_r_{u_id}")
                            
                            col_sub1, col_sub2 = st.columns(2)
                            with col_sub1:
                                guardar_cambios = st.form_submit_button("💾 Guardar")
                            with col_sub2:
                                cancelar_cambios = st.form_submit_button("❌ Cancelar")

                            if guardar_cambios:
                                if mod_nombre and mod_pass:
                                    try:
                                        supabase.table("usuarios").update({
                                            "usuario": mod_nombre,
                                            "password": mod_pass,
                                            "rol_id": mod_rol
                                        }).eq("id", u_id).execute()
                                        st.session_state[f"edit_mode_{u_id}"] = False
                                        st.success("✅ Actualizado.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                            if cancelar_cambios:
                                st.session_state[f"edit_mode_{u_id}"] = False
                                st.rerun()
                    st.divider()
            else:
                st.info("Sin usuarios registrados.")
        except Exception as e:
            st.error(f"Error al cargar usuarios: {e}")
