supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
return supabase.storage.from_(bucket).get_public_url(path)
from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN Y ESTILO VISUAL (MODO OSCURO)
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# CSS personalizado para diseño profesional de fondo oscuro, tipografía nítida y estados a color
st.markdown("""
    <style>
    /* Fondo principal y textos */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Contenedores y expanders generales */
    div.streamlit-expanderHeader {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        color: #f9fafb;
        font-weight: 600;
    }
    
    /* Tarjetas y bloques de formularios */
    div[data-testid="stForm"] {
        background-color: #111827;
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Etiquetas y textos generales */
    p, label, span, div {
        color: #e5e7eb;
    }
    
    /* Botones principales llamativos */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        box-shadow: 0 6px 8px -1px rgba(59, 130, 246, 0.4);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #030712;
        border-right: 1px solid #1f2937;
    }
    </style>
""", unsafe_allow_html=True)

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/octet-stream", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión"]
roles_disponibles = [
"Administrador", "Recepción", "Diseñador", "Almacén", 
"Producción - Bordados", "Producción - Impresión"
]

# ==========================================
# GESTIÓN DE SESIÓN
@@ -28,79 +31,202 @@ def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.update({"autenticado": False, "usuario": "", "rol": ""})

st.sidebar.title("🔐 Control de Acceso")
if not st.session_state["autenticado"]:
usuario_input = st.sidebar.text_input("Usuario")
password_input = st.sidebar.text_input("Contraseña", type="password")
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
    if st.sidebar.button("Iniciar Sesión"):
if usuario_input.strip().lower() == "admin" and password_input == "2580Admin":
st.session_state.update({"autenticado": True, "usuario": "admin", "rol": "Administrador"})
st.rerun()
@@ -38,7 +102,7 @@
st.sidebar.error("❌ Usuario o contraseña incorrectos.")
except Exception as e:
st.sidebar.error(f"Error: {e}")
st.stop()
    st.stop()

# ==========================================
# PANEL PRINCIPAL
@@ -53,14 +117,6 @@
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
st.subheader("📋 Listado y Control de Órdenes")
try:
ordenes = supabase.table("ordenes").select("*").execute().data
@@ -70,37 +126,23 @@

if ordenes:
ordenes_a_mostrar = [o for o in ordenes if (o.get('estado') or o.get('estado_actual')) in estados_filtro] if estados_filtro else ordenes

            # Formulario de actualización
            with st.form(f"form_update_{o.get('id')}"):
                nuevo_estado = st.selectbox("Cambiar estado", lista_estados, index=lista_estados.index(estado_actual) if estado_actual in lista_estados else 0)
                if st.form_submit_button("💾 Actualizar y Registrar Cambio"):
                    # 1. Actualizar estado
                    supabase.table("ordenes").update({"estado": nuevo_estado}).eq("id", o.get("id")).execute()
            
for o in ordenes_a_mostrar:
estado_actual = o.get('estado') or o.get('estado_actual') or 'Pendiente'

                with st.expander(f"Orden #{o.get('numero_orden', 'N/A')} - Cliente: {o.get('nombre_cliente', 'N/A')} | Estado: {estado_actual}"):
                # Asignación de colores distintivos según el estado de la orden
                color_map = {
                    "Pendiente": "🟡",
                    "Enviado a Recepción": "🔵",
                    "En Producción": "🟠",
                    "Regresado a Recepción": "🟣",
                    "Orden Entregada": "🟢"
                }
                icono_estado = color_map.get(estado_actual, "⚪")
                
                with st.expander(f"{icono_estado} Orden #{o.get('numero_orden', 'N/A')} - Cliente: {o.get('nombre_cliente', 'N/A')} | Estado: {estado_actual}"):
st.write(f"**Área:** {o.get('area_produccion', 'N/A')} | **Detalles:** {o.get('nombre_orden', 'N/A')}")

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
                    
# Formulario para actualizar estado
with st.form(f"form_update_{o.get('id')}"):
nuevo_estado = st.selectbox(
@@ -111,38 +153,31 @@
)

if st.form_submit_button("💾 Actualizar y Registrar Cambio"):
                            # 1. Actualizar estado en la tabla de órdenes
                            fecha_hora_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                            usuario_actual = st.session_state['usuario']
                            
                            nuevo_registro = f"• Estado: **{nuevo_estado}** | Usuario: `{usuario_actual}` | Fecha: {fecha_hora_str}"
                            historial_previo = o.get('historial') or ""
                            historial_actualizado = f"{nuevo_registro}\n{historial_previo}" if historial_previo else nuevo_registro
                            
supabase.table("ordenes").update({
"estado": nuevo_estado, 
                                "estado_actual": nuevo_estado
                                "estado_actual": nuevo_estado,
                                "historial": historial_actualizado
}).eq("id", o.get("id")).execute()

                            # 2. Registrar en el historial de cambios
                            supabase.table("historial_ordenes").insert({
                                "orden_id": str(o.get('id')),
                                "nuevo_estado": nuevo_estado,
                                "usuario_que_cambio": st.session_state['usuario'],
                                "fecha_hora": datetime.now().isoformat()
                            }).execute()
                            
                            st.success("✅ Estado actualizado y registrado correctamente.")
                            st.success("✅ Estado actualizado correctamente.")
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
                        historial_texto = o.get('historial')
                        if historial_texto:
                            st.markdown(historial_texto)
                        else:
                            st.info("No hay cambios registrados en el historial para esta orden.")
else:
st.info("No hay órdenes registradas.")
except Exception as e:
@@ -152,15 +187,10 @@
# TAB 1: NUEVA ORDEN
# ------------------------------------------
with tabs[1]:
with st.form("form_nueva_orden", clear_on_submit=True):
        cliente = st.text_input("Cliente")
        nombre_ord = st.text_input("Detalles")
    with st.form("form_nueva_orden", clear_on_submit=True):
cliente = st.text_input("Nombre del Cliente")
nombre_ord = st.text_input("Nombre de la Orden / Detalles")
area = st.selectbox("Área", ["Bordados", "Impresion"])
        if st.form_submit_button("Guardar"):
            supabase.table("ordenes").insert({"numero_orden": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}", "nombre_cliente": cliente, "nombre_orden": nombre_ord, "area_produccion": area, "estado": "Pendiente"}).execute()
            st.success("✅ Orden creada.")
        area = st.selectbox("Área", ["Bordados", "Impresion"])
archivos = st.file_uploader("Subir Archivos", accept_multiple_files=True)

if st.form_submit_button("Guardar Orden"):
@@ -175,20 +205,18 @@
"area_produccion": area,
"imagen_url": ",".join(urls),
"estado": "Pendiente",
                    "estado_actual": "Pendiente"
                    "estado_actual": "Pendiente",
                    "historial": f"• Creada como **Pendiente** | Usuario: `{st.session_state['usuario']}` | Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
}).execute()
st.success("✅ Orden creada con éxito.")
except Exception as e:
st.error(f"Error: {e}")

# ------------------------------------------
# TAB 2: GESTIÓN DE USUARIOS
# TAB 2: GESTIÓN DE USUARIOS (ADMIN)
# ------------------------------------------
with tabs[2]:
if st.session_state['rol'] == "Administrador":
        # ... (Tu código anterior de gestión de usuarios) ...
        st.write("Panel de administrador activo.")
    if st.session_state['rol'] == "Administrador":
st.subheader("👥 Registrar Nuevo Usuario")
with st.form("reg_user", clear_on_submit=True):
n_nombre = st.text_input("Nombre Completo")
@@ -259,6 +287,5 @@
st.info("No hay usuarios registrados en la base de datos.")
except Exception as e:
st.error(f"Error al cargar la lista de usuarios: {e}")
else:
        st.error("Acceso restringido.")
    else:
st.error("⛔ Acceso restringido. Esta sección es exclusiva para Administradores.")
