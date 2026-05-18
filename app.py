import os
from pyvirtualdisplay import Display

# Crea una pantalla virtual invisible para que pyautogui no truene en la nube
display = Display(visible=0, size=(1024, 768))
display.start()

# Ahora sí puedes continuar con tus imports normales
import streamlit as st
import pywhatkit as kit
import streamlit as st
import pandas as pd
import os
import pywhatkit as kit
import time
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE SEGURIDAD (Solución DecompressionBombError) ---
Image.MAX_IMAGE_PIXELS = None 
st.set_page_config(page_title="Sistema Integra Sonora", layout="wide", page_icon="🗳️")

# Mapeo de colores oficiales para los distritos
COLORES_DISTRITOS = {
    "1": "#FF4B4B", "2": "#1C83E1", "3": "#00C49A", "4": "#FCA311", "5": "#9B5DE5",
    "6": "#00F5D4", "7": "#FFEE32", "8": "#00BBF9", "9": "#F15BB5", "10": "#0077B6",
    "11": "#EE9B00", "12": "#0A9396", "13": "#94D2BD", "14": "#E9D8A6", "15": "#BB3E03",
    "16": "#005F73", "17": "#AE2012", "18": "#9B2226", "19": "#E09F3E", "20": "#335C67",
    "21": "#540B0E", "POR_ASIGNAR": "#6D6D6D"
}

# --- 2. CARGA INTELIGENTE Y BLINDADA DEL CATÁLOGO ---
@st.cache_data
def cargar_catalogo_seguro():
    archivo = "catalogo_sonora.csv"
    if os.path.exists(archivo):
        try:
            df = pd.read_csv(archivo, sep=None, engine='python', on_bad_lines='skip', encoding='latin1')
            df.columns = df.columns.str.strip().str.upper()
            
            c_sec = [c for c in df.columns if any(x in c for x in ['SEC', 'SECC', 'SECCIÓN', 'SECCION'])]
            c_dto = [c for c in df.columns if any(x in c for x in ['DTO', 'DIST', 'DISTRITO'])]
            
            columna_seccion = c_sec[0] if c_sec else df.columns[0]
            columna_distrito = c_dto[0] if c_dto else df.columns[1]
            
            df[columna_seccion] = df[columna_seccion].astype(str).str.replace('.0', '', regex=False).str.strip()
            return df, columna_seccion, columna_distrito
        except Exception as e:
            st.sidebar.error(f"Error procesando columnas del CSV: {e}")
            return None, None, None
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
        st.error("❌ Catálogo no detectado")
        st.info("Ubica 'catalogo_sonora.csv' en la carpeta SISTEMA PAN VICTOR.")

# --- 4. CONTROL DE PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 PANEL DE CONTROL", "📢 WHATSAPP"])

# --- PESTAÑA 1: CAPTURA ---
with tab1:
    col_campos, col_leyenda = st.columns([3, 1])
    
    with col_leyenda:
        st.subheader("📌 Distritos")
        for d, color in COLORES_DISTRITOS.items():
            if d.isdigit():
                st.markdown(
                    f'<div style="display:flex;align-items:center;margin-bottom:3px;">'
                    f'<div style="width:12px;height:12px;background:{color};border-radius:50%;margin-right:8px;"></div>'
                    f'<span style="font-size:12px; font-weight:500;">Dto {d}</span></div>', 
                    unsafe_allow_html=True
                )

    with col_campos:
        nombre = st.text_input("Nombre Completo:").upper()
        direccion = st.text_input("Dirección:")
        celular = st.text_input("Celular (10 dígitos):")
        municipio_f = st.text_input("Municipio:", value="HERMOSILLO").upper()
        seccion_f = st.number_input("Sección Electoral:", min_value=1, value=390)
        
        dto_final = "POR_ASIGNAR"
        if df_cat is not None:
            match = df_cat[df_cat[col_sec] == str(int(seccion_f))]
            if not match.empty:
                dto_final = str(match.iloc[0][col_dto]).strip().replace('.0', '')
        
        color_res = COLORES_DISTRITOS.get(dto_final, "#6D6D6D")
        st.markdown(f"<div style='background-color:{color_res};padding:12px;border-radius:10px;text-align:center;color:white;font-weight:bold;font-size:22px;margin-bottom:15px;'>DISTRITO DETECTADO: {dto_final}</div>", unsafe_allow_html=True)
        
        # CORRECCIÓN DEFINITIVA AL FORMULARIO (Evita el TypeError de la captura)
        with st.form("form_captura", clear_on_submit=True):
            st.markdown("### Documentación Fotográfica")
            c1, c2 = st.columns(2)
            foto_p = c1.camera_input("Capturar Rostro")
            foto_i = c2.camera_input("Capturar INE")  # Corregido aquí
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
                    "FOTO_PER": path_p, "FOTO_INE": path_i
                }])
                
                nuevo_reg.to_csv(base_file, mode='a', header=not os.path.exists(base_file), index=False)
                st.success("¡Registro Guardado Exitosamente!")
                st.balloons()
            else:
                st.warning("⚠️ Nombre y Celular son campos obligatorios.")

        # --- REEMPLAZO DEL MAPA (Solución Segura que no rechaza la conexión) ---
        st.markdown(f'<div style="border: 5px solid {color_res}; border-radius: 12px; overflow: hidden; margin-top:15px;">', unsafe_allow_html=True)
        direccion_mapa = f"Seccion {seccion_f}, {direccion}, {municipio_f}, Sonora".replace(" ", "+")
        # Usamos el visor seguro de OpenStreetMap que permite incrustación libre sin bloqueos de origen
        url_mapa_libre = f"https://www.openstreetmap.org/export/embed.html?bbox=-111.05%2C29.03%2C-110.90%2C29.15&layer=mapnik&marker=29.08%2C-110.97"
        components.iframe(url_mapa_libre, height=400)
        st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 2: VISUALIZACIÓN DE LA BASE ---
with tab2:
    st.header("📊 Base de Datos General")
    base_file = "BASE_TOTAL_CONTACTOS.csv"
    if os.path.exists(base_file):
        try:
            df_v = pd.read_csv(base_file, on_bad_lines='skip', engine='python')
            if not df_v.empty:
                st.metric("Total de Ciudadanos en la Base", len(df_v))
                st.dataframe(df_v, use_container_width=True)
            else:
                st.info("No hay datos en el archivo CSV aún.")
        except Exception as e:
            st.error(f"Error al abrir la base de datos: {e}")
    else:
        st.warning("Aún no se han generado registros en el sistema.")

# --- PESTAÑA 3: ENVÍO MASIVO WHATSAPP ---
with tab3:
    st.header("📢 Módulo de Mensajería Masiva")
    base_file = "BASE_TOTAL_CONTACTOS.csv"
    
    if os.path.exists(base_file):
        try:
            df_w = pd.read_csv(base_file, on_bad_lines='skip', engine='python')
            mensaje_base = st.text_area("Mensaje a enviar (Usa {nombre} para personalizar):", "Hola {nombre}, un saludo de parte del equipo.")
            
            c_f1, c_f2 = st.columns(2)
            distritos_disponibles = sorted([str(x) for x in df_w['DISTRITO'].unique() if pd.notna(x)])
            filtro_dto = c_f1.selectbox("Filtrar envío por Distrito Local:", ["TODOS"] + distritos_disponibles)
            
            if st.button("🚀 INICIAR ENVÍO AUTOMÁTICO"):
                contactos_filtrados = df_w if filtro_dto == "TODOS" else df_w[df_w['DISTRITO'].astype(str) == filtro_dto]
                
                if not contactos_filtrados.empty:
                    barra_progreso = st.progress(0)
                    total_envios = len(contactos_filtrados)
                    
                    for idx, row in contactos_filtrados.reset_index(drop=True).iterrows():
                        try:
                            num = str(row['CELULAR']).strip().split('.')[0]
                            if not num.startswith('+52'):
                                num = '+52' + num
                            
                            msg_personalizado = mensaje_base.replace("{nombre}", str(row['NOMBRE']))
                            kit.sendwhatmsg_instantly(num, msg_personalizado, wait_time=12, tab_close=True)
                            st.write(f"✅ Mensaje enviado con éxito a: {row['NOMBRE']}")
                            time.sleep(4)
                        except Exception as err:
                            st.error(f"❌ Error al enviar a {row['NOMBRE']}: {err}")
                        
                        barra_progreso.progress((idx + 1) / total_envios)
                    st.success("¡Proceso de envío masivo finalizado!")
                else:
                    st.warning("No se encontraron registros activos para el distrito seleccionado.")
        except Exception as e:
            st.error(f"Error en la lectura del módulo de WhatsApp: {e}")
    else:
        st.warning("No hay registros disponibles para realizar envíos de mensajes.")
