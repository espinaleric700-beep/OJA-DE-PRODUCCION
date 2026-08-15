from datetime import datetime
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def subir_a_supabase(file_bytes, file_name, bucket="disenos"):
    path = f"ordenes/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}"
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "image/jpeg", "upsert": "true"})
    return supabase.storage.from_(bucket).get_public_url(path)

# ==========================================
# AUTENTICACIÓN
# ==========================================
st.sidebar.title("🔐 Control de Acceso")
usuario = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")
roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]
rol_seleccionado = st.sidebar.selectbox("Rol", roles_disponibles)

if rol_seleccionado == "Administrador":
    if st.sidebar.text_input("Clave de Administrador", type="password") != "2580Admin":
        st.sidebar.error("Clave incorrecta")
        st.stop()
if not usuario:
    st.warning("Ingresa tu usuario")
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🧵 Pixel Thread - Gestión de Órdenes")
ordenes_db = supabase.table("ordenes").select("*").execute().data
busqueda = st.text_input("🔍 Buscador")

mapa_roles = {
    "Recepción": ["Creada / Pendiente de Diseño", "Enviado a Transferencia Térmica"],
    "Diseñador": ["Creada / Pendiente de Diseño"],
    "Almacén": ["Enviado a Recepción"],
    "Producción - Bordados": ["En Producción"],
    "Producción - Impresión": ["En Producción"],
    "Transferencia Térmica": ["Enviado a Transferencia Térmica"]
}

if rol_seleccionado == "Administrador":
    tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
else:
    tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

with tab1:
    for o in ordenes_db:
        # FILTRO: Ocultar canceladas
        if o["estado_actual"] == "Cancelado": continue
        
        if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and busqueda.lower() not in o.get("nombre_cliente", "").lower()):
            continue

        with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**"):
            st.write(f"**Cliente:** {o['nombre_cliente']} | **Entrega:** {o.get('fecha_entrega', 'N/A')}")
            
            # Lógica de Cancelación
            if rol_seleccionado in ["Administrador", "Recepción", "Diseñador"]:
                with st.popover("❌ Cancelar Orden"):
                    motivo = st.text_area("Motivo de la cancelación")
                    if st.checkbox("Confirmar cancelación"):
                        if st.button("Ejecutar Cancelación", key=f"cancel_{o['id']}"):
                            supabase.table("ordenes").update({"estado_actual": "Cancelado"}).eq("id", o["id"]).execute()
                            supabase.table("historial_ordenes").insert({
                                "orden_id": o["id"], "estado_anterior": o["estado_actual"], 
                                "estado_nuevo": "CANCELADO", "cambiado_por": usuario, "motivo": motivo
                            }).execute()
                            st.rerun()
            
            # Botones de estado (omitidos por brevedad, usar la lógica anterior)
            # ... (Aquí irían tus botones de transición de estado) ...

with tab2:
    with st.form("form_nueva_orden"):
        nombre_cliente = st.text_input("Cliente")
        nombre_orden = st.text_input("Nombre de la Orden")
        area = st.selectbox("Área", ["Bordados", "Impresion"])
        fecha = st.date_input("Fecha de Entrega")
        if st.form_submit_button("Crear"):
            num = f"ORD-{len(ordenes_db)+1:03d}"
            supabase.table("ordenes").insert({
                "numero_orden": num, "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                "area_produccion": area, "fecha_entrega": str(fecha),
                "estado_actual": "Creada / Pendiente de Diseño", "creado_por": usuario
            }).execute()
            st.rerun()

if rol_seleccionado == "Administrador":
    with tab3:
        # Formulario registro usuario
        st.subheader("👥 Registrar Usuario")
        n_user = st.text_input("Usuario", key="n_u")
        n_pass = st.text_input("Password", type="password", key="n_p")
        n_rol = st.selectbox("Rol", roles_disponibles, key="n_r")
        if st.button("Registrar"):
            supabase.table("usuarios").insert({"usuario": n_user, "password": n_pass, "rol": n_rol}).execute()
            st.success("Registrado")
        
        st.subheader("📊 Historial (Incluye Cancelaciones)")
        try:
            historial = supabase.table("historial_ordenes").select("*").execute().data
            st.dataframe(historial)
        except: st.info("Historial vacío.")
