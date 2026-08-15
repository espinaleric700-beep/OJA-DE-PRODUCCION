with tabs[2]:
    st.subheader("📦 Control de Inventario")
    puede_modificar = st.session_state['rol'] in ["Administrador", "Recepción", "Almacén"]

    if puede_modificar:
        with st.expander("➕ Agregar Nuevo Producto con Colores, Tallas e Imagen por Color", expanded=False):
            inv_nombre = st.text_input("NOMBRE DE LA PRENDA", key="input_nombre_prenda_color_img")
            st.markdown("---")
            st.markdown("🎨 **Añadir Color, Tono y su Imagen Correspondiente**")
            
            col_picker, col_text = st.columns([1, 2])
            with col_picker:
                color_picker_val = st.color_picker("Tono", "#3b82f6", key="picker_color_hex_v2")
            with col_text:
                nuevo_color = st.text_input("NOMBRE O CÓDIGO DEL COLOR", value=color_picker_val, key="input_nuevo_color_nombre_v2")
            
            foto_color = st.file_uploader(f"🖼️ Subir Imagen para el color: `{nuevo_color}`", type=["png", "jpg", "jpeg"], key=f"uploader_img_{nuevo_color}")
            
            if st.button("➕ Añadir este Color al Producto"):
                if nuevo_color.strip():
                    c_clean = nuevo_color.strip()
                    if c_clean not in st.session_state["colores_inventario_avanzado"]:
                        st.session_state["colores_inventario_avanzado"][c_clean] = {
                            "tallas": {t: 0 for t in tallas_disponibles},
                            "imagen_file": foto_color,
                            "hex": color_picker_val if color_picker_val.startswith("#") else "#3b82f6"
                        }
                        st.success(f"Color '{c_clean}' agregado con éxito.")
                        st.rerun()
                    else:
                        st.warning("Este color ya está en la lista.")
                else:
                    st.error("Ingresa un nombre o código de color válido.")

            if st.session_state["colores_inventario_avanzado"]:
                st.markdown("#### 🔍 Configurar Existencias y Tallas por Color:")
                color_activo = st.selectbox("Selecciona color a configurar:", list(st.session_state["colores_inventario_avanzado"].keys()), key="select_color_activo_v2")
                
                if color_activo:
                    st.markdown(f"📏 **Tallas para `{color_activo}`**")
                    cols_grid = st.columns(3)
                    for idx, talla in enumerate(tallas_disponibles):
                        col_actual = cols_grid[idx % 3]
                        with col_actual:
                            val_actual = st.session_state["colores_inventario_avanzado"][color_activo]["tallas"].get(talla, 0)
                            nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=int(val_actual), key=f"cant_v2_{color_activo}_{talla}")
                            st.session_state["colores_inventario_avanzado"][color_activo]["tallas"][talla] = int(nueva_cant)
                            
                    if st.button("🗑️ Eliminar este color", key=f"del_col_v2_{color_activo}"):
                        del st.session_state["colores_inventario_avanzado"][color_activo]
                        st.rerun()

            st.markdown("---")
            if st.button("💾 Guardar Inventario Completo"):
                if not inv_nombre.strip():
                    st.error("⚠️ Debes ingresar el nombre del producto.")
                elif not st.session_state["colores_inventario_avanzado"]:
                    st.error("⚠️ Debes agregar al menos un color con sus tallas e imágenes.")
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
                        st.success("✅ ¡Producto guardado con éxito!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar producto: {e}")
        st.divider()

    try:
        # Consulta directa y fresca a Supabase para evitar datos cacheados
        inventario_db = supabase.table("almacen").select("*").execute().data
        if inventario_db:
            st.markdown("### 📋 Existencias Actuales en Almacén")
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
                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                            else:
                                dict_colores = temp_data
                except Exception:
                    dict_colores = {}

                st.markdown(f"### 🏷️ {p_nombre}")
                
                if dict_colores:
                    lista_cols = list(dict_colores.keys())
                    key_activo = f"color_activo_prod_{item_id}"
                    
                    if key_activo not in st.session_state or st.session_state[key_activo] not in lista_cols:
                        st.session_state[key_activo] = lista_cols[0]
                    
                    st.markdown("Colores")
                    cols_colores = st.columns(min(len(lista_cols), 4))
                    for idx, c_name in enumerate(lista_cols):
                        with cols_colores[idx % len(cols_colores)]:
                            if st.button(c_name, key=f"btn_color_item_{item_id}_{c_name}", use_container_width=True):
                                st.session_state[key_activo] = c_name
                                st.rerun()
                    
                    color_sel = st.session_state[key_activo]
                    data_color = dict_colores.get(color_sel, {})
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        if data_color.get("imagen_url"): 
                            st.image(data_color["imagen_url"], use_container_width=True)
                        else:
                            st.info("Sin imagen para este color")
                            
                    with col_info:
                        st.markdown(f"**Existencias para el color: `{color_sel}`**")
                        tallas_del_color = data_color.get("tallas", {})
                        
                        columna_1 = ["2", "4", "6", "8", "10"]
                        columna_2 = ["12", "14", "16", "S", "M"]
                        columna_3 = ["WS", "WM", "L", "XL", "2XL"]
                        
                        grid_cols = st.columns(3)
                        grupos_tallas = [columna_1, columna_2, columna_3]
                        
                        for col_idx, grupo in enumerate(grupos_tallas):
                            with grid_cols[col_idx]:
                                for talla in grupo:
                                    cantidad = int(tallas_del_color.get(talla, 0))
                                    if puede_modificar:
                                        sub1, sub2 = st.columns([1.2, 2.0])
                                        with sub1:
                                            st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='font-size: 0.85em; font-weight: bold; color: #4ade80;'>{talla}</span></div>", unsafe_allow_html=True)
                                        with sub2:
                                            # Usamos la cantidad fresca directamente de la base de datos como valor por defecto
                                            nueva_cant = st.number_input(f"Talla {talla}", min_value=0, step=1, value=cantidad, key=f"num_{item_id}_{color_sel}_{talla}", label_visibility="collapsed")
                                            if nueva_cant != cantidad:
                                                dict_colores[color_sel]["tallas"][talla] = int(nueva_cant)
                                                # Guardamos inmediatamente en Supabase
                                                supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                                # Forzamos un reseteo de la clave del input para limpiar la caché local y propagar el cambio
                                                st.rerun()
                                    else:
                                        st.markdown(f"<div style='background-color: #111827; padding: 6px; border-radius: 4px; border: 1px solid #1f2937; text-align: center;'><span style='color: #4ade80;'>{talla}</span>: <b>{cantidad:02d}</b></div>", unsafe_allow_html=True)
                                    st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Formato de colores estructurado no válido.")

                if puede_modificar:
                    with st.expander(f"🛠️ Gestionar Colores e Imagen de: {p_nombre}"):
                        nueva_img_file = st.file_uploader(f"Nueva imagen para `{color_sel}`", type=["png", "jpg", "jpeg"], key=f"up_img_prod_{item_id}_{color_sel}")
                        if st.button("💾 Guardar Nueva Imagen", key=f"btn_save_img_{item_id}_{color_sel}"):
                            if nueva_img_file is not None:
                                try:
                                    url_subida = subir_a_supabase(nueva_img_file.getvalue(), nueva_img_file.name)
                                    dict_colores[color_sel]["imagen_url"] = url_subida
                                    supabase.table("almacen").update({"tallas_existencias": json.dumps(dict_colores)}).eq("id", item_id).execute()
                                    st.success("✅ ¡Imagen actualizada!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            else:
                                st.warning("Selecciona una imagen primero.")
                        
                        if st.button("🗑️ Eliminar Producto Completo", key=f"del_prod_item_{item_id}"):
                            supabase.table("almacen").delete().eq("id", item_id).execute()
                            st.warning("⚠️ Producto eliminado.")
                            st.rerun()
                st.divider()
        else:
            st.info("No hay productos registrados en el almacén.")
    except Exception as e:
        st.error(f"Error al cargar almacén: {e}")
