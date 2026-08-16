import streamlit as st
import os
import json
from supabase import create_client

# --- 1. CONFIGURACIÓN ROBUSTA ---
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        # Fallback para desarrollo local
        from dotenv import load_dotenv
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Credenciales no configuradas. Revisa tus Secrets en Streamlit Cloud.")
        st.stop()
    return create_client(url, key)

supabase = init_supabase()
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# --- 2. ESTADO INICIAL ---
if "colores_inventario_avanzado" not in st.session_state:
    st.session_state["colores_inventario_avanzado"] = {}
tallas_disponibles = ["XS", "S", "M", "L", "XL", "XXL"]

# --- 3. INTERFAZ ---
tabs = st.tabs(["Dashboard", "Órdenes", "Almacén"])

with tabs[2]:
    st.subheader("📦 Control de Inventario")
    
    # SECCIÓN: AGREGAR PRODUCTO
    with st.expander("➕ Agregar Nuevo Producto"):
        inv_nombre = st.text_input("NOMBRE DE LA PRENDA")
        nuevo_color = st.text_input("NOMBRE DEL COLOR (Ej: NEGRO, BLANCO)")
        
        if st.button("➕ Añadir Color"):
            if nuevo_color.strip():
                st.session_state["colores_inventario_avanzado"][nuevo_color.upper()] = {
                    "tallas": {t: 0 for t in tallas_disponibles}
                }
                st.rerun()

        for col in st.session_state["colores_inventario_avanzado"]:
            st.write(f"**Color: {col}**")
            cols = st.columns(6)
            for i, t in enumerate(tallas_disponibles):
                st.session_state["colores_inventario_avanzado"][col]["tallas"][t] = cols[i].number_input(t, value=0, key=f"new_{col}_{t}")

        if st.button("💾 Guardar Inventario en DB"):
            supabase.table("almacen").insert({
                "nombre_producto": inv_nombre.upper(),
                "tallas_existencias": json.dumps(st.session_state["colores_inventario_avanzado"])
            }).execute()
            st.session_state["colores_inventario_avanzado"] = {}
            st.success("¡Guardado exitosamente!")
            st.rerun()

    # SECCIÓN: INVENTARIO EXISTENTE (EDICIÓN MANUAL)
    st.markdown("---")
    st.subheader("📋 Inventario Actual")
    
    try:
        res_inv = supabase.table("almacen").select("*").execute()
        if res_inv.data:
            for prod in res_inv.data:
                p_id = prod["id"]
                dict_existencias = json.loads(prod["tallas_existencias"])
                
                with st.container(border=True):
                    st.write(f"### 🏷️ {prod['nombre_producto']}")
                    color_sel = st.selectbox("Seleccionar Color", list(dict_existencias.keys()), key=f"sel_{p_id}")
                    
                    tallas_data = dict_existencias[color_sel]["tallas"]
                    cols = st.columns(6)
                    updated_tallas = {}
                    
                    # Campos editables
                    for i, t in enumerate(tallas_disponibles):
                        updated_tallas[t] = cols[i].number_input(
                            f"{t}", 
                            value=int(tallas_data.get(t, 0)), 
                            key=f"edit_{p_id}_{color_sel}_{t}"
                        )
                    
                    # Botón de Guardado Individual
                    if st.button(f"💾 Actualizar Stock: {color_sel}", key=f"btn_{p_id}_{color_sel}"):
                        dict_existencias[color_sel]["tallas"] = updated_tallas
                        supabase.table("almacen").update({
                            "tallas_existencias": json.dumps(dict_existencias)
                        }).eq("id", p_id).execute()
                        st.success(f"Stock de {color_sel} actualizado.")
                        st.rerun()
    except Exception as e:
        st.warning("Cargando inventario o vacío...")
