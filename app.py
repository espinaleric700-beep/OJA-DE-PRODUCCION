import streamlit as st
from supabase import create_client
import os
import json
from dotenv import load_dotenv

# --- CONFIGURACIÓN ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuración de página
st.set_page_config(page_title="Pixel Thread - Gestión", layout="wide")

# Inicialización de estado
if "colores_inventario_avanzado" not in st.session_state:
    st.session_state["colores_inventario_avanzado"] = {}
if "rol" not in st.session_state:
    st.session_state["rol"] = "Administrador" # Ajusta según tu lógica de login

tallas_disponibles = ["XS", "S", "M", "L", "XL", "XXL"]

# --- FUNCIÓN DE SUBIDA (SIMPLIFICADA) ---
def subir_a_supabase(file_bytes, file_name):
    # Aquí iría tu lógica de storage de Supabase
    return "url_de_la_imagen_subida"

# --- INTERFAZ ---
tabs = st.tabs(["Dashboard", "Órdenes", "Almacén"])

# --- TAB 3: ALMACÉN (CON EDICIÓN MANUAL) ---
with tabs[2]:
    st.subheader("📦 Control de Inventario")
    
    # 1. SECCIÓN DE AGREGAR PRODUCTO
    with st.expander("➕ Agregar Nuevo Producto"):
        inv_nombre = st.text_input("NOMBRE DE LA PRENDA")
        nuevo_color = st.text_input("NOMBRE DEL COLOR")
        
        if st.button("➕ Añadir Color a la Lista"):
            c_clean = nuevo_color.strip().upper()
            st.session_state["colores_inventario_avanzado"][c_clean] = {
                "tallas": {t: 0 for t in tallas_disponibles},
                "imagen_url": ""
            }
            st.rerun()

        # Edición de stock para el nuevo producto
        for col in st.session_state["colores_inventario_avanzado"]:
            st.write(f"**Color: {col}**")
            cols = st.columns(6)
            for i, t in enumerate(tallas_disponibles):
                st.session_state["colores_inventario_avanzado"][col]["tallas"][t] = cols[i].number_input(t, value=0, key=f"new_{col}_{t}")

        if st.button("💾 Guardar Inventario Completo"):
            supabase.table("almacen").insert({
                "nombre_producto": inv_nombre.upper(),
                "tallas_existencias": json.dumps(st.session_state["colores_inventario_avanzado"])
            }).execute()
            st.session_state["colores_inventario_avanzado"] = {}
            st.success("¡Guardado!")
            st.rerun()

    # 2. SECCIÓN DE INVENTARIO EXISTENTE (EDICIÓN MANUAL)
    st.markdown("---")
    st.subheader("📋 Inventario Actual")
    res_inv = supabase.table("almacen").select("*").execute()
    
    if res_inv.data:
        for prod in res_inv.data:
            p_id = prod["id"]
            dict_existencias = json.loads(prod["tallas_existencias"])
            
            with st.container(border=True):
                st.write(f"### {prod['nombre_producto']}")
                color_sel = st.selectbox("Seleccionar Color", list(dict_existencias.keys()), key=f"sel_{p_id}")
                
                # Matriz editable de tallas
                tallas_data = dict_existencias[color_sel]["tallas"]
                cols = st.columns(6)
                updated_tallas = {}
                
                for i, t in enumerate(tallas_disponibles):
                    updated_tallas[t] = cols[i].number_input(
                        f"Talla {t}", 
                        value=int(tallas_data.get(t, 0)), 
                        key=f"edit_{p_id}_{color_sel}_{t}"
                    )
                
                if st.button(f"💾 Actualizar Stock: {color_sel}", key=f"btn_{p_id}_{color_sel}"):
                    dict_existencias[color_sel]["tallas"] = updated_tallas
                    supabase.table("almacen").update({
                        "tallas_existencias": json.dumps(dict_existencias)
                    }).eq("id", p_id).execute()
                    st.success("¡Stock actualizado!")
                    st.rerun()
