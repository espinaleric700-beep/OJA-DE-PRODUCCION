if rol_seleccionado == "Administrador":
    with tab3:
        st.subheader("👥 Gestión de Usuarios y Roles del Sistema")
        nuevo_usuario_input = st.text_input("Nuevo Usuario")
        nuevo_password_input = st.text_input("Contraseña del Usuario", type="password")
        rol_nuevo_input = st.selectbox("Rol Asignado", roles_disponibles, key="select_rol_nuevo")
        
        if st.button("Registrar Usuario"):
            if nuevo_usuario_input and nuevo_password_input:
                try:
                    supabase.table("usuarios").insert({
                        "usuario": nuevo_usuario_input, 
                        "password": nuevo_password_input, 
                        "rol": rol_nuevo_input
                    }).execute()
                    st.success(f"Usuario {nuevo_usuario_input} registrado con éxito.")
                except Exception as e:
                    st.error(f"Error al registrar usuario (asegúrate de que la tabla 'usuarios' tenga las columnas 'usuario', 'password' y 'rol'): {e}")
            else:
                st.warning("Por favor completa el usuario y la contraseña.")
        
        st.markdown("---")
        st.subheader("📊 Historial de Órdenes Registradas")
        try:
            historial_db = supabase.table("historial_ordenes").select("*").execute().data
            if historial_db:
                st.dataframe(historial_db)
            else:
                st.info("No hay registros en el historial todavía.")
        except:
            st.info("La tabla 'historial_ordenes' no está configurada o está vacía en Supabase.")
