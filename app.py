from datetime import datetime
import os
import firebase_admin
from firebase_admin import credentials, storage
import streamlit as st
from supabase import create_client

# ==========================================
# CONFIGURACIÓN DE CONEXIONES
# ==========================================
st.set_page_config(
    page_title="Sistema de Órdenes - Pixel Thread",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializar Supabase
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# Inicializar Firebase Storage
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace(
                "\\n", "\n"
            ),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"][
                "auth_provider_x509_cert_url"
            ],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        cred = credentials.Certificate(cred_dict)
        bucket_name = st.secrets["firebase"]["bucket_name"]
        firebase_admin.initialize_app(
            cred, {"storageBucket": bucket_name}
        )


init_firebase()


def subir_a_firebase(file_bytes, file_name, folder="ordenes/"):
    bucket_name = st.secrets["firebase"]["bucket_name"]
    bucket = storage.bucket(bucket_name)
    blob = bucket.blob(f"{folder}{datetime.now().strftime('%Y%m%d%H%M%S')}_{file_name}")
    blob.upload_from_string(file_bytes)
    blob.make_public()
    return blob.public_url


# ==========================================
# AUTENTICACIÓN Y ROLES
# ==========================================
st.sidebar.title("🔐 Control de Acceso")
usuario = st.sidebar.text_input("Usuario")
password = st.sidebar.text_input("Contraseña", type="password")

roles_disponibles = [
    "Administrador",
    "Recepción",
    "Diseñador",
    "Almacén",
    "Producción - Bordados",
    "Producción - Impresión",
    "Transferencia Térmica",
]
rol_seleccionado = st.sidebar.selectbox("Rol", roles_disponibles)

# Validación de clave para el rol Administrador
if rol_seleccionado == "Administrador":
    clave_admin = st.sidebar.text_input("Clave de Administrador", type="password")
    if clave_admin != "2580Admin":
        st.sidebar.error("Clave de Administrador incorrecta.")
        st.stop()

if not usuario:
    st.warning("Por favor, ingresa tu usuario para continuar.")
    st.stop()

# ==========================================
# PANEL PRINCIPAL
# ==========================================
st.title("🧵 Pixel Thread - Gestión de Órdenes")

# Buscador Inteligente Global
busqueda = st.text_input(
    "🔍 Buscador rápido (Número de orden, Cliente o Nombre de orden)"
)

# Pestañas de Navegación
tab1, tab2, tab3 = st.tabs(
    [
        "📋 Ver Órdenes",
        "➕ Nueva Orden",
        "⚙️ Configuración / Reportes / Usuarios",
    ]
)

with tab1:
    st.subheader("Listado de Órdenes Activas")

    # Obtener órdenes de Supabase
    response = supabase.table("ordenes").select("*").execute()
    ordenes = response.data

    if ordenes:
        for o in ordenes:
            # Aplicar filtro de búsqueda
            if busqueda and (
                busqueda.lower() not in o.get("numero_orden", "").lower()
                and busqueda.lower() not in o.get("nombre_cliente", "").lower()
                and busqueda.lower() not in o.get("nombre_orden", "").lower()
            ):
                continue

            with st.expander(
                f"Orden: {o['numero_orden']} | Cliente: {o['nombre_cliente']} | Estado: **{o['estado_actual']}**"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nombre de Referencia:** {o['nombre_orden']}")
                    st.write(f"**Área:** {o['area_produccion']}")
                    st.write(f"**Fecha Creación:** {o['fecha_creacion']}")
                    st.write(
                        f"**Fecha Entrega:** {o.get('fecha_entrega', 'No asignada')}"
                    )
                    if rol_seleccionado in ["Administrador", "Recepción"]:
                        st.info(f"**Nota Interna:** {o.get('nota_interna', 'Ninguna')}")

                with col2:
                    # Mostrar múltiples archivos de diseño si existen
                    if o.get("archivo_diseno"):
                        st.markdown("**Archivos de Diseño:**")
                        archivos = o["archivo_diseno"].split(",")
                        for idx, url in enumerate(archivos):
                            if url.strip():
                                st.markdown(f"- [Descargar Diseño {idx + 1}]({url.strip()})")

                    # Mostrar recibo de pago (solo visible para Admin y Recepción)
                    if rol_seleccionado in ["Administrador", "Recepción"]:
                        if o.get("recibo_pago"):
                            st.markdown(f"[Ver Recibo de Pago]({o['recibo_pago']})")

                # Flujo de Estados y Botón Verde de Acción
                estado = o["estado_actual"]
                nuevo_estado = estado

                if estado == "Creada / Pendiente de Diseño" and rol_seleccionado in [
                    "Administrador",
                    "Recepción",
                    "Diseñador",
                ]:
                    if st.button(
                        "🟢 Avanzar: Enviar a Recepción", key=f"btn_{o['id']}"
                    ):
                        nuevo_estado = "Enviado a Recepción"

                elif (
                    estado == "Enviado a Recepción"
                    and rol_seleccionado in ["Administrador", "Recepción"]
                ):
                    if st.button("🟢 Avanzar: Enviar a Almacén", key=f"btn_{o['id']}"
                    ):
                        nuevo_estado = "Enviado a Almacén"

                elif (
                    estado == "Enviado a Almacén"
                    and rol_seleccionado in ["Administrador", "Almacén"]
                ):
                    if st.button("🟢 Avanzar: Enviar a Producción", key=f"btn_{o['id']}"
                    ):
                        nuevo_estado = "En Producción"

                elif estado == "En Producción":
                    if (
                        o["area_produccion"] == "Bordados"
                        and rol_seleccionado
                        in ["Administrador", "Producción - Bordados"]
                    ):
                        if st.button(
                            "🟢 Marcar como Completado", key=f"btn_bordado_{o['id']}"
                        ):
                            nuevo_estado = "Completado"
                    elif (
                        o["area_produccion"] == "Impresion"
                        and rol_seleccionado
                        in ["Administrador", "Producción - Impresión"]
                    ):
                        if st.button(
                            "🟢 Avanzar: Enviado a Transferencia Térmica",
                            key=f"btn_imp_{o['id']}",
                        ):
                            nuevo_estado = "Enviado a Transferencia Térmica"

                elif estado == "Enviado a Transferencia Térmica" and rol_seleccionado in [
                    "Administrador",
                    "Transferencia Térmica",
                ]:
                    if st.button(
                        "🟢 Avanzar: Enviado a Recepción", key=f"btn_term_{o['id']}"
                    ):
                        nuevo_estado = "Enviado a Recepción"

                elif estado in ["Completado", "Enviado a Recepción"] and rol_seleccionado in [
                    "Administrador",
                    "Recepción",
                ]:
                    # Solo permitimos entregar si ya está completado o devuelto a recepción por transferencia térmica
                    if estado in ["Completado", "Enviado a Recepción"] and o.get("area_produccion") == "Impresion" and estado == "Enviado a Recepción":
                        if st.button("🟢 Marcar como Entregado (Fin)", key=f"btn_fin_{o['id']}"
                        ):
                            nuevo_estado = "Entregado"
                    elif estado == "Completado" and o.get("area_produccion") == "Bordados":
                        if st.button("🟢 Marcar como Entregado (Fin)", key=f"btn_fin_{o['id']}"
                        ):
                            nuevo_estado = "Entregado"

                # Actualizar estado en Supabase si cambió
                if nuevo_estado != estado:
                    supabase.table("ordenes").update(
                        {"estado_actual": nuevo_estado}
                    ).eq("id", o["id"]).execute()

                    # Registrar en historial
                    supabase.table("historial_ordenes").insert({
                        "orden_id": o["id"],
                        "estado_anterior": estado,
                        "estado_nuevo": nuevo_estado,
                        "cambiado_por": usuario,
                        "fecha_hora": datetime.now().isoformat(),
                    }).execute()
                    st.success("¡Estado actualizado con éxito!")
                    st.rerun()
    else:
        st.info("No hay órdenes registradas.")

with tab2:
    st.subheader("Crear Nueva Orden de Trabajo")

    with st.form("form_nueva_orden"):
        nombre_cliente = st.text_input("Nombre del Cliente")
        nombre_orden = st.text_input("Nombre de la Orden / Referencia")
        area_produccion = st.selectbox(
            "Área de Producción", ["Bordados", "Impresion"]
        )

        fecha_entrega = None
        if rol_seleccionado in ["Administrador", "Recepción"]:
            fecha_entrega = st.date_input(
                "Fecha estimada de entrega (Solo Admin y Recepción)"
            )

        nota_interna = st.text_area(
            "Nota Interna (Solo Admin y Recepción)"
        )

        archivos_subidos = st.file_uploader(
            "Subir Archivos de Diseño (Puedes seleccionar varios: .emb, .dst, .cdr,"
            " .ai, .pdf, etc.)",
            type=[
                "jpg",
                "png",
                "pdf",
                "psd",
                "ai",
                "eps",
                "cdr",
                "emb",
                "dst",
                "tbf",
            ],
            accept_multiple_files=True,
        )

        recibo_subido = None
        if rol_seleccionado in ["Administrador", "Recepción"]:
            recibo_subido = st.file_uploader(
                "Subir Recibo de Pago (Solo Admin y Recepción)",
                type=["jpg", "png", "pdf"],
            )

        submit = st.form_submit_button("Crear Orden")

        if submit:
            if nombre_cliente and nombre_orden:
                urls_diseno = []
                url_recibo = ""

                if archivos_subidos:
                    for archivo in archivos_subidos:
                        url = subir_a_firebase(
                            archivo.getvalue(), archivo.name, "disenos/"
                        )
                        urls_diseno.append(url)

                if recibo_subido and rol_seleccionado in ["Administrador", "Recepción"]:
                    url_recibo = subir_a_firebase(
                        recibo_subido.getvalue(), recibo_subido.name, "recibos/"
                    )

                num_orden = f"ORD-{datetime.now().strftime('%Y')}-{int(datetime.now().timestamp()) % 10000}"

                nueva_fila = {
                    "numero_orden": num_orden,
                    "nombre_cliente": nombre_cliente,
                    "nombre_orden": nombre_orden,
                    "area_produccion": area_produccion,
                    "estado_actual": "Creada / Pendiente de Diseño",
                    "fecha_creacion": datetime.now().isoformat(),
                    "fecha_entrega": (
                        str(fecha_entrega) if fecha_entrega else None
                    ),
                    "nota_interna": nota_interna,
                    "archivo_diseno": ",".join(urls_diseno),
                    "recibo_pago": url_recibo,
                    "creado_por": usuario,
                }

                supabase.table("ordenes").insert(nueva_fila).execute()
                st.success(f"¡Orden {num_orden} creada correctamente!")
                st.rerun()
            else:
                st.error("Por favor completa los campos obligatorios.")

with tab3:
    st.subheader("👥 Gestión de Usuarios y Roles")

    if rol_seleccionado != "Administrador":
        st.warning(
            "Solo el Administrador puede gestionar usuarios y roles."
        )
    else:
        with st.expander("➕ Registrar Nuevo Usuario"):
            with st.form("form_nuevo_usuario"):
                nuevo_nombre = st.text_input("Nombre Completo del Empleado")
                nuevo_usuario = st.text_input("Nombre de Usuario (Login)")
                nuevo_password = st.text_input("Contraseña", type="password")
                nuevo_rol = st.selectbox("Asignar Rol", roles_disponibles)

                submit_usuario = st.form_submit_button("Registrar Usuario")

                if submit_usuario:
                    if nuevo_nombre and nuevo_usuario and nuevo_password:
                        try:
                            supabase.table("usuarios").insert({
                                "nombre": nuevo_nombre,
                                "usuario": nuevo_usuario,
                                "password": nuevo_password,
                                "rol_id": roles_disponibles.index(nuevo_rol) + 1,
                            }).execute()
                            st.success(
                                f"¡Usuario '{nuevo_usuario}' registrado con rol '{nuevo_rol}'"
                                " con éxito!"
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar usuario: {e}")
                    else:
                        st.error("Por favor completa todos los campos.")

    st.divider()
    st.subheader("✏️ Modificar o Eliminar Usuarios Existentes")

    usuarios_res = supabase.table("usuarios").select("*").execute()
    lista_usuarios = usuarios_res.data

    if lista_usuarios:
        for u in lista_usuarios:
            with st.expander(
                f"Usuario: {u['usuario']} - Nombre: {u['nombre']}"
            ):
                with st.form(f"form_mod_{u['id']}"):
                    mod_nombre = st.text_input(
                        "Nombre Completo", value=u["nombre"], key=f"nombre_{u['id']}"
                    )
                    mod_password = st.text_input(
                        "Nueva Contraseña",
                        value=u["password"],
                        type="password",
                        key=f"pass_{u['id']}",
                    )
                    current_rol_index = (
                        u["rol_id"] - 1
                        if 0 <= u["rol_id"] - 1 < len(roles_disponibles)
                        else 0
                    )
                    mod_rol = st.selectbox(
                        "Rol",
                        roles_disponibles,
                        index=current_rol_index,
                        key=f"rol_{u['id']}",
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    actualizar = col_btn1.form_submit_button("Actualizar Usuario")
                    eliminar = col_btn2.form_submit_button("Eliminar Usuario")

                    if actualizar:
                        supabase.table("usuarios").update({
                            "nombre": mod_nombre,
                            "password": mod_password,
                            "rol_id": roles_disponibles.index(mod_rol) + 1,
                        }).eq("id", u["id"]).execute()
                        st.success("¡Usuario actualizado con éxito!")
                        st.rerun()

                    if eliminar:
                        supabase.table("usuarios").delete().eq(
                            "id", u["id"]
                        ).execute()
                        st.success("¡Usuario eliminado con éxito!")
                        st.rerun()
    else:
        st.info(
            "No hay usuarios registrados en la base de datos o la tabla está"
            " vacía."
        )

    st.divider()
    st.subheader("📋 Auditoría e Historial de Cambios")
    historial = (
        supabase.table("historial_ordenes")
        .select("*")
        .order("fecha_hora", desc=True)
        .limit(50)
        .execute()
    )
    if historial.data:
        st.dataframe(historial.data)
    else:
        st.info("No hay registros en el historial todavía.")
