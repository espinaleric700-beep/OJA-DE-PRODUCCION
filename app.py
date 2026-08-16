       border-color: #58a6ff !important;
   }

    /* Estilos para las tarjetas contenedoras con borde */
   div[data-testid="stVerticalBlockBorderWrapper"] {
       background-color: rgba(22, 27, 34, 0.75) !important;
       border: 1px solid #30363d !important;
@@ -112,7 +111,6 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
       box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
   }

    /* Ajuste para imágenes PNG transparentes sobre el fondo oscuro de la app */
   [data-testid="stImage"] {
       display: flex;
       justify-content: center;
@@ -129,23 +127,22 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
       filter: drop-shadow(0px 8px 16px rgba(0, 0, 0, 0.45));
   }

    /* Inputs de números más compactos y organizados */
   div[data-testid="stNumberInput"] {
       background: rgba(22, 27, 34, 0.85);
       border: 1px solid #30363d;
        border-radius: 6px;
        padding: 2px 4px;
        margin-bottom: 2px;
        border-radius: 8px;
        padding: 4px 6px;
        margin-bottom: 4px;
   }
   div[data-testid="stNumberInput"] label {
        font-size: 0.70rem !important;
        font-size: 0.75rem !important;
       color: #8b949e !important;
       font-weight: 700;
       text-transform: uppercase;
   }
   div[data-testid="stNumberInput"] input {
        height: 28px !important;
        font-size: 0.82rem !important;
        height: 32px !important;
        font-size: 0.88rem !important;
       background-color: transparent !important;
       color: #ffffff !important;
       text-align: center;
@@ -161,7 +158,6 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
       border: 1px solid #30363d;
   }

    /* Tabla personalizada de tallas */
   .sizes-table {
       width: 100%;
       border-collapse: collapse;
@@ -182,9 +178,34 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
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
            max-height: 320px !important;
            max-height: 380px !important;
           object-fit: contain !important;
       }
   }
@@ -194,7 +215,7 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
           padding: 0.5rem 0.5rem 2rem 0.5rem !important;
       }
       [data-testid="stImage"] img {
            max-height: 200px !important;
            max-height: 210px !important;
           object-fit: contain !important;
       }
       div[data-testid="stRadio"] > div {
@@ -204,7 +225,6 @@ def keep_server_alive_loop(app_url, interval_seconds=300):
   </style>
""", unsafe_allow_html=True)

# Detectar ancho de la pantalla dinámicamente
ancho_pantalla = streamlit_js_eval(js_expressions='window.innerWidth', key='viewport_width')
es_movil = (ancho_pantalla < 768) if ancho_pantalla is not None else False

@@ -411,40 +431,81 @@ def obtener_badge_estado(estado):
st.markdown("👕 **Detalle de Tallas / Sizes:**")
try:
lista_tallas = json.loads(tallas_db) if isinstance(tallas_db, str) else tallas_db
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
                            
                            # Botón de activación para editar tallas manualmente
                            edit_mode_key = f"edit_tallas_mode_{o_id}"
                            if edit_mode_key not in st.session_state:
                                st.session_state[edit_mode_key] = False

                            if st.session_state['rol'] in ["Administrador", "Recepción", "Producción - Bordados", "Almacén"]:
                                if st.button("✏️ Editar Tallas y Cantidades", key=f"btn_toggle_edit_tallas_{o_id}"):
                                    st.session_state[edit_mode_key] = not st.session_state[edit_mode_key]
                                    st.rerun()

                            if st.session_state[edit_mode_key]:
                                st.info("Modo de edición manual activo:")
                                nuevo_detalle_tallas = []
                                with st.form(key=f"form_edit_tallas_{o_id}"):
                                    # Asegurarnos de tener una estructura base editable con las tallas disponibles o las existentes
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
                                        supabase.table("ordenes").update({"tallas_detalle": json.dumps(temp_tallas_actualizadas)}).eq("id", o_id).execute()
                                        st.session_state[edit_mode_key] = False
                                        st.success("¡Tallas actualizadas correctamente!")
                                        st.rerun()
else:
                                st.caption("No hay desglose de tallas registrado.")
                        except Exception:
                            st.caption("No se registró información de tallas.")
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
@@ -588,14 +649,14 @@ def obtener_badge_estado(estado):
st.rerun()

# ==============================================================================
# TAB 3: ALMACÉN (VERSIÓN ANTERIOR: IMAGEN ARRIBA / DISEÑO ORIGINAL)
# TAB 3: ALMACÉN
# ==============================================================================
with tabs[2]:
st.subheader("📦 Control de Inventario")
puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

if puede_modificar:
        with st.expander("➕ Agregar Producto / Existencias", expanded=False):
        with st.expander("➕ Agregar Producto", expanded=False):
inv_nombre = st.text_input("NOMBRE DE LA PRENDA", key="input_nombre_prenda_color_img")
st.markdown("---")
st.markdown("🎨 **Añadir Color e Imagen**")
@@ -630,13 +691,13 @@ def obtener_badge_estado(estado):

if color_activo:
st.markdown(f"📏 **Tallas para `{color_activo}`**")
                    cols_grid = st.columns(3 if es_movil else 6)
                    cols_grid = st.columns(2 if es_movil else 5)
num_cols = len(cols_grid)
for idx, talla in enumerate(tallas_disponibles):
col_actual = cols_grid[idx % num_cols]
with col_actual:
val_actual = st.session_state["colores_inventario_avanzado"][color_activo]["tallas"].get(talla, 0)
                            nueva_cant = st.number_input(f"T. {talla}", min_value=0, step=1, value=int(val_actual), key=f"cant_v2_{color_activo}_{talla}")
                            nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=int(val_actual), key=f"cant_v2_{color_activo}_{talla}")
st.session_state["colores_inventario_avanzado"][color_activo]["tallas"][talla] = int(nueva_cant)

if st.button("🗑️ Eliminar color", key=f"del_col_v2_{color_activo}"):
@@ -666,135 +727,126 @@ def obtener_badge_estado(estado):

supabase.table("almacen").insert({
"nombre_producto": inv_nombre,
                            "tallas_existencias": json.dumps(data_a_guardar),
                            "imagen_url": ""
                            "tallas_existencias": json.dumps(data_a_guardar)
}).execute()
                        
st.success("¡Inventario guardado con éxito!")
st.session_state["colores_inventario_avanzado"] = {}
st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar el inventario: {e}")
                    except Exception as err:
                        st.error(f"Error al guardar inventario: {err}")

    # ==========================================================================
    # SECCIÓN DE VISUALIZACIÓN DE INVENTARIO (DISEÑO ORIGINAL: IMAGEN ARRIBA)
    # ==========================================================================
    st.markdown("### 📊 Existencias Actuales")
    st.markdown("---")
    st.subheader("📦 Productos en Inventario")
try:
res_inv = supabase.table("almacen").select("*").execute()
if res_inv.data:
for prod in res_inv.data:
p_id = prod.get("id")
p_nombre = prod.get("nombre_producto", "Sin Nombre")
                tallas_ext_db = prod.get("tallas_existencias", "{}")
                p_tallas_raw = prod.get("tallas_existencias", "{}")

try:
                    dict_existencias = json.loads(tallas_ext_db) if isinstance(tallas_ext_db, str) else tallas_ext_db
                except:
                    dict_existencias = {}
                    p_datos = json.loads(p_tallas_raw) if isinstance(p_tallas_raw, str) else p_tallas_raw
                except: p_datos = {}

with st.container(border=True):
                    st.markdown(f"🏷️ **{p_nombre}**")
                    
                    if dict_existencias:
                        colores_keys = list(dict_existencias.keys())
                        color_seleccionado = st.radio(
                            "Selecciona Color:", 
                            colores_keys, 
                            key=f"radio_color_inv_{p_id}", 
                            horizontal=True
                        )
                        
                        if color_seleccionado and color_seleccionado in dict_existencias:
                            info_color = dict_existencias[color_seleccionado]
                            tallas_dict = info_color.get("tallas", {})
                            img_url_prod = info_color.get("imagen_url", "")
                            
                            st.markdown("---")
                            # DISEÑO ORIGINAL: Imagen arriba y abajo las tallas
                            if img_url_prod:
                                st.image(img_url_prod, use_container_width=True)
                            
                            st.markdown(f"📏 **Tallas Disponibles (`{color_seleccionado}`):**")
                    col_p_info, col_p_img = st.columns([3, 1])
                    with col_p_info:
                        st.markdown(f"### {p_nombre}")
                        if p_datos:
                            colores_disponibles_list = list(p_datos.keys())
                            color_seleccionado_ver = st.selectbox("Color", colores_disponibles_list, key=f"sel_ver_color_{p_id}")

                            cols_grid_tallas = st.columns(4 if es_movil else 8)
                            num_g_cols = len(cols_grid_tallas)
                            
                            for t_idx, talla_item in enumerate(tallas_disponibles):
                                cant_stock = tallas_dict.get(talla_item, 0)
                                col_celda = cols_grid_tallas[t_idx % num_g_cols]
                                with col_celda:
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(22, 27, 34, 0.9); border: 1px solid #30363d; border-radius: 6px; padding: 6px; text-align: center; margin-bottom: 6px;">
                                            <div style="font-size: 0.75rem; color: #8b949e; font-weight: bold; text-transform: uppercase;">{talla_item}</div>
                                            <div style="font-size: 1.15rem; color: #58a6ff; font-weight: bold;">{cant_stock}</div>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                    else:
                        st.caption("No hay colores ni tallas configuradas para este producto.")
                            if color_seleccionado_ver in p_datos:
                                info_color = p_datos[color_seleccionado_ver]
                                tallas_dict = info_color.get("tallas", {})
                                
                                # Renderizar tabla de inventario grid
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
                                
                                img_url_color = info_color.get("imagen_url", "")
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
                                st.error(f"Error al eliminar: {ex}")
else:
            st.info("No hay productos registrados en el almacén.")
            st.caption("No hay productos registrados en el almacén.")
except Exception as e:
        st.error(f"Error al cargar el inventario: {e}")
        st.error(f"Error al cargar almacén: {e}")

# ==============================================================================
# TAB 4: USUARIOS
# ==============================================================================
with tabs[3]:
    st.subheader("⚙️ Gestión de Usuarios y Accesos")
    st.subheader("⚙️ Gestión de Usuarios")
if st.session_state['rol'] == "Administrador":
with st.form("form_crear_usuario"):
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                nuevo_usuario = st.text_input("Nombre de Usuario")
            with col_u2:
                nuevo_password = st.text_input("Contraseña", type="password")
            with col_u3:
                nuevo_rol = st.selectbox("Rol Asignado", roles_disponibles)
            u_nombre = st.text_input("Nombre de Usuario")
            u_pass = st.text_input("Contraseña", type="password")
            u_rol = st.selectbox("Rol del Usuario", roles_disponibles)

if st.form_submit_button("➕ Registrar Usuario"):
                if nuevo_usuario.strip() and nuevo_password.strip():
                if u_nombre.strip() and u_pass.strip():
try:
supabase.table("usuarios").insert({
                            "usuario": nuevo_usuario.strip(),
                            "password": nuevo_password.strip(),
                            "rol_id": nuevo_rol
                            "usuario": u_nombre.strip(),
                            "password": u_pass.strip(),
                            "rol_id": u_rol
}).execute()
                        st.success(f"Usuario '{nuevo_usuario}' creado con éxito.")
                        st.success(f"Usuario '{u_nombre}' creado con éxito.")
st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear usuario: {e}")
                    except Exception as err:
                        st.error(f"Error al registrar usuario: {err}")
else:
                    st.error("Completa todos los campos.")
                    st.warning("Completa todos los campos.")

st.markdown("---")
        st.markdown("#### 👥 Usuarios Registrados:")
        st.markdown("### 📋 Usuarios Registrados")
try:
            res_usuarios = supabase.table("usuarios").select("*").execute()
            if res_usuarios.data:
                for usr in res_usuarios.data:
            res_u = supabase.table("usuarios").select("*").execute()
            if res_u.data:
                for usr in res_u.data:
u_id = usr.get("id")
                    u_name = usr.get("usuario")
                    u_rol = usr.get("rol_id")
                    u_n = usr.get("usuario")
                    u_r = usr.get("rol_id")

                    col_info_u, col_del_u = st.columns([3, 1])
                    with col_info_u:
                        st.markdown(f"👤 **{u_name}** — Rol: *{u_rol}*")
                    with col_del_u:
                        if u_name.lower() != "admin":
                            if st.button("🗑️ Eliminar", key=f"btn_del_usr_{u_id}"):
                                try:
                                    supabase.table("usuarios").delete().eq("id", u_id).execute()
                                    st.success("Usuario eliminado.")
                                    st.rerun()
                                except Exception as err:
                                    st.error(f"Error: {err}")
                    col_u1, col_u2 = st.columns([3, 1])
                    with col_u1:
                        st.write(f"👤 **{u_n}** — Rol: *{u_r}*")
                    with col_u2:
                        if u_n.lower() != "admin":
                            if st.button("🗑️ Eliminar", key=f"del_user_{u_id}"):
                                supabase.table("usuarios").delete().eq("id", u_id).execute()
                                st.rerun()
else:
                st.info("No hay usuarios adicionales registrados.")
                st.caption("No hay usuarios adicionales registrados.")
except Exception as e:
st.error(f"Error al listar usuarios: {e}")
else:
        st.warning("⚠️ Acceso restringido solo para Administradores.")
        st.warning("⚠️ No tienes permisos de Administrador para ver esta sección.")
