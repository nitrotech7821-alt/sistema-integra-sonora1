import os

# --- IMPORTS DEL SISTEMA ---
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components
import urllib.parse

# --- BLINDAGE TOTAL PARA MAPAS ---
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except Exception:
    FOLIUM_AVAILABLE = False

# --- BLINDAGE TOTAL PARA WHATSAPP ---
try:
    import pywhatkit as kit
    PYWHATKIT_AVAILABLE = True
except Exception:
    PYWHATKIT_AVAILABLE = False

# --- 1. CONFIGURACIÓN ---
Image.MAX_IMAGE_PIXELS = None 
st.set_page_config(page_title="Sistema Integra Sonora", layout="wide", page_icon="🗳️")

COLORES_DISTRITOS = {
    "1": "#FF4B4B", "2": "#1C83E1", "3": "#00C49A", "4": "#FCA311", "5": "#9B5DE5",
    "6": "#00F5D4", "7": "#FFEE32", "8": "#00BBF9", "9": "#F15BB5", "10": "#0077B6",
    "11": "#EE9B00", "12": "#0A9396", "13": "#94D2BD", "14": "#E9D8A6", "15": "#BB3E03",
    "16": "#005F73", "17": "#AE2012", "18": "#9B2226", "19": "#E09F3E", "20": "#335C67",
    "21": "#540B0E", "POR_ASIGNAR": "#6D6D6D"
}

LAT_HERMOSILLO = 29.0729
LON_HERMOSILLO = -110.9559

# --- 2. CARGA DEL CATÁLOGO ---
@st.cache_data
def cargar_catalogo_seguro():
    archivo = "catalogo_sonora.csv"
    if os.path.exists(archivo):
        try:
            try:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            except:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
            
            df.columns = df.columns.str.strip().str.upper()
            col_sec, col_dto = None, None
            
            for col in df.columns:
                if any(x in col for x in ['SEC', 'SECC', 'SECCION', 'SECCIÓN', 'NUM_SEC']): col_sec = col
                if any(x in col for x in ['DTO', 'DIST', 'DISTRITO', 'LOCAL']): col_dto = col

            if col_sec and col_dto:
                df[col_sec] = df[col_sec].astype(str).str.replace('.0', '', regex=False).str.strip()
                return df, col_sec, col_dto
            else:
                if len(df.columns) >= 2:
                    df.columns = ['SECCION', 'DISTRITO'] + list(df.columns[2:])
                    df['SECCION'] = df['SECCION'].astype(str).str.replace('.0', '', regex=False).str.strip()
                    return df, 'SECCION', 'DISTRITO'
        except Exception:
            pass
    return None, None, None

df_cat, col_sec, col_dto = cargar_catalogo_seguro()

# --- 3. PANEL LATERAL ---
with st.sidebar:
    if os.path.exists("logo_pan_sonora.jpg"):
        st.image("logo_pan_sonora.jpg", use_container_width=True)
    st.markdown("---")
    if df_cat is not None:
        st.success("✅ Catálogo Sonora Conectado")
    else:
        st.warning("⚠️ Catálogo no detectado")

# --- 4. PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 PANEL DE CONTROL", "📢 WHATSAPP"])

with tab1:
    col_campos, col_mapa_panel = st.columns([2, 2])
    
    with col_campos:
        nombre = st.text_input("Nombre Completo:").upper()
        direccion = st.text_input("Dirección:")
        celular = st.text_input("Celular (10 dígitos):")
        municipio_f = st.text_input("Municipio:", value="HERMOSILLO").upper()
        seccion_f = st.number_input("Sección Electoral:", min_value=1, value=390)
        
        dto_final = "POR_ASIGNAR"
        lat_seccion = LAT_HERMOSILLO
        lon_seccion = LON_HERMOSILLO
        
        if df_cat is not None:
            match = df_cat[df_cat[col_sec] == str(int(seccion_f))]
            if not match.empty:
                dto_final = str(match.iloc[0][col_dto]).strip().replace('.0', '')
        
        if dto_final == "POR_ASIGNAR" or dto_final not in COLORES_DISTRITOS:
            dto_final = st.selectbox("Distrito Local (No detectado automáticamente):", list(COLORES_DISTRITOS.keys()))
        
        color_res = COLORES_DISTRITOS.get(dto_final, "#6D6D6D")
        st.markdown(f"<div style='background-color:{color_res};padding:12px;border-radius:10px;text-align:center;color:white;font-weight:bold;font-size:22px;margin-bottom:15px;'>DISTRITO DETECTADO: {dto_final}</div>", unsafe_allow_html=True)
        
        with st.form("form_captura", clear_on_submit=True):
            st.markdown("### Documentación Fotográfica")
            c1, c2 = st.columns(2)
            with c1: foto_p = st.camera_input("Capturar Rostro")
            with c2: foto_i = st.camera_input("Capturar INE")
            btn_guardar = st.form_submit_button("💾 GUARDAR REGISTRO")

        if btn_guardar:
            if nombre and celular:
                if not os.path.exists("fotos_captura"): os.makedirs("fotos_captura")
                if not os.path.exists("fotos_ine"): os.makedirs("fotos_ine")
                path_p = f"fotos_captura/F_{celular}.png"
                path_i = f"fotos_ine/I_{celular}.png"
                if foto_p: Image.open(foto_p).save(path_p)
                if foto_i: Image.open(foto_i).save(path_i)
                
                base_file = "BASE_TOTAL_CONTACTOS.csv"
                nuevo_reg = pd.DataFrame([{
                    "FECHA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "NOMBRE": nombre, "DIRECCION": direccion, "CELULAR": celular,
                    "MUNICIPIO": municipio_f, "SECCION": seccion_f, "DISTRITO": dto_final,
                    "LATITUD": lat_seccion, "LONGITUD": lon_seccion,
                    "FOTO_PER": path_p, "FOTO_INE": path_i
                }])
                nuevo_reg.to_csv(base_file, mode='a', header=not os.path.exists(base_file), index=False)
                st.success("¡Registro Guardado Exitosamente!")
                st.balloons()
                st.rerun()

    with col_mapa_panel:
        st.subheader("🗺️ Ubicación Georreferenciada")
        if FOLIUM_AVAILABLE:
            try:
                m = folium.Map(location=[lat_seccion, lon_seccion], zoom_start=13)
                folium.Marker([lat_seccion, lon_seccion], popup=f"Sección: {seccion_f}").add_to(m)
                st_folium(m, width=500, height=450, key="mapa_reg_safe")
            except Exception:
                st.info("Cargando vista del mapa de respaldo...")
        else:
            # Mapa estático de respaldo si la nube no tiene folium instalado aún
            url_mapa_respaldo = f"https://www.openstreetmap.org/export/embed.html?bbox=-111.02%2C29.05%2C-110.92%2C29.12&layer=mapnik"
            components.iframe(url_mapa_respaldo, height=450)

with tab2:
    st.header("📊 Base de Datos General")
    base_file = "BASE_TOTAL_CONTACTOS.csv"
    if os.path.exists(base_file):
        try:
            df_v = pd.read_csv(base_file, on_bad_lines='skip', engine='python')
            if not df_v.empty:
                st.metric("Total de Ciudadanos en la Base", len(df_v))
                st.dataframe(df_v, use_container_width=True)
        except Exception:
            st.error("Esperando nuevos registros...")

with tab3:
    st.header("📢 Módulo de Mensajería")
    base_file = "BASE_TOTAL_CONTACTOS.csv"
    if os.path.exists(base_file):
        try:
            df_w = pd.read_csv(base_file, on_bad_lines='skip', engine='python')
            mensaje_base = st.text_area("Mensaje a enviar (Usa {nombre} para personalizar):", "Hola {nombre}, un saludo.")
            
            distritos_disponibles = sorted([str(x) for x in df_w['DISTRITO'].unique() if pd.notna(x)])
            filtro_dto = st.selectbox("Filtrar envío por Distrito Local:", ["TODOS"] + distritos_disponibles)
            contactos_filtrados = df_w if filtro_dto == "TODOS" else df_w[df_w['DISTRITO'].astype(str) == filtro_dto]
            
            if not contactos_filtrados.empty:
                for idx, row in contactos_filtrados.reset_index(drop=True).iterrows():
                    num = str(row['CELULAR']).strip().split('.')[0]
                    if not num.startswith('52'): num = '52' + num
                    msg_personalizado = mensaje_base.replace("{nombre}", str(row['NOMBRE']))
                    texto_url = urllib.parse.quote(msg_personalizado)
                    url_wa = f"https://api.whatsapp.com/send?phone={num}&text={texto_url}"
                    
                    c_n, c_b = st.columns([3, 1])
                    c_n.write(f"👤 **{row['NOMBRE']}** ({row['CELULAR']})")
                    c_b.markdown(f'[@ Enviar por WhatsApp]({url_wa})', unsafe_allow_html=True)
        except Exception:
            pass
