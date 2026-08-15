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

# ==========================================
# AUTENTICACIÓN
# ==========================================
st.sidebar.title("🔐 Control de Acceso")
usuario = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")
roles_disponibles = ["Administrador", "Recepción", "Diseñador", "Almacén", "Producción - Bordados", "Producción - Impresión", "Transferencia Térmica"]
rol_seleccionado = st.sidebar.selectbox("Rol", roles_disponibles)

# Roles con permisos de creación y modificación
ROLES_AUTORIZADOS = ["Administrador", "Recepción", "Diseñador"]

if rol_seleccionado == "Administrador":
    if st.sidebar.text_input("Clave de Administrador", type="password") != "2580Admin":
        st.sidebar.error("Clave incorrecta")
        st.stop()
if not usuario:
    st.warning("Por favor ingresa tu usuario")
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🧵 Pixel Thread - Gestión de Órdenes")
ordenes_db = supabase.table("ordenes").select("*").execute().data
busqueda = st.text_input("🔍 Buscador rápido (Número o Cliente)")

# Configuración de pestañas
if rol_seleccionado == "Administrador":
    tab1, tab2, tab3 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden", "⚙️ Configuración / Usuarios"])
else:
    tab1, tab2 = st.tabs(["📋 Ver Órdenes", "➕ Nueva Orden"])

with tab1:
    for o in ordenes_db:
        # FILTRO: No mostrar canceladas
        if o["estado_actual"] == "Cancelado": continue
        
        if busqueda and (busqueda.lower() not in o.get("numero_orden", "").lower() and busqueda.lower() not in o.get("nombre_cliente", "").lower()):
            continue

        with st.expander(f"Orden: {o['numero_orden']} | Estado: **{o['estado_actual']}**"):
            st.write(f"**Cliente:** {o['nombre_cliente']} | **Área:** {o['area_produccion']} | **Fecha Entrega:** {o.get('fecha_entrega', 'N/A')}")
            
            # ACCIONES (Solo autorizados)
            if rol_seleccionado in ROLES_AUTORIZADOS:
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    with st.popover("❌ Cancelar"):
                        motivo = st.text_area("Motivo de la cancelación")
                        if st.checkbox("Confirmar cancelación"):
                            if st.button("Ejecutar", key=f"conf_cancel_{o['id']}"):
                                supabase.table("ordenes").update({"estado_actual": "Cancelado"}).eq("id", o["id"]).execute()
                                supabase.table("historial_ordenes").insert({
                                    "orden_id": o["id"], "estado_anterior": o["estado_actual"], 
                                    "estado_nuevo": "CANCELADO", "motivo": motivo, "cambiado_por": usuario
                                }).execute()
                                st.rerun()
            
            # --- Aquí puedes añadir tus botones de estados (Ej: Enviar a Producción) ---
            # ...

with tab2:
    if rol_seleccionado in ROLES_AUTORIZADOS:
        with st.form("form_nueva_orden"):
            nombre_cliente = st.text_input("Cliente")
            nombre_orden = st.text_input("Nombre de la Orden")
            area = st.selectbox("Área", ["Bordados", "Impresion"])
            fecha = st.date_input("Fecha de Entrega")
            if st.form_submit_button("Crear Nueva Orden"):
                num = f"ORD-{len(ordenes_db)+1:03d}"
                supabase.table("ordenes").insert({
                    "numero_orden": num, "nombre_cliente": nombre_cliente, "nombre_orden": nombre_orden,
                    "area_produccion": area, "fecha_entrega": str(fecha),
                    "estado_actual": "Creada / Pendiente de Diseño", "creado_por": usuario
                }).execute()
                st.success(f"Orden {num} creada")
                st.rerun()
    else:
        st.error("⚠️ No tienes permisos para crear o modificar órdenes. Contacta a un administrador.")

# TAB ADMIN
if rol_seleccionado == "Administrador":
    with tab3:
        st.subheader("👥 Gestión de Usuarios")
        n_user = st.text_input("Nuevo Usuario")
        n_pass = st.text_input("Contraseña", type="password")
        n_rol = st.selectbox("Rol", roles_disponibles)
        if st.button("Registrar"):
            supabase.table("usuarios").insert({"usuario": n_user, "password": n_pass, "rol": n_rol}).execute()
            st.success("Usuario registrado")
        
        st.markdown("---")
        st.subheader("📊 Historial de Movimientos y Cancelaciones")
        try:
            historial = supabase.table("historial_ordenes").select("*").execute().data
            st.dataframe(historial)
        except:
            st.info("No hay registros en el historial.")
