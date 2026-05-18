import os

# --- IMPORTS DEL SISTEMA ---
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from PIL import Image
import streamlit.components.v1 as components
import urllib.parse  # Para crear enlaces de WhatsApp válidos en la nube

# Intentamos importar pywhatkit de forma segura
try:
    import pywhatkit as kit
    PYWHATKIT_AVAILABLE = True
except Exception as e:
    PYWHATKIT_AVAILABLE = False

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
Image.MAX_IMAGE_PIXELS = None 
st.set_page_config(page_title="Sistema Integra Sonora", layout="wide", page_icon="🗳️")

COLORES_DISTRITOS = {
    "1": "#FF4B4B", "2": "#1C83E1", "3": "#00C49A", "4": "#FCA311", "5": "#9B5DE5",
    "6": "#00F5D4", "7": "#FFEE32", "8": "#00BBF9", "9": "#F15BB5", "10": "#0077B6",
    "11": "#EE9B00", "12": "#0A9396", "13": "#94D2BD", "14": "#E9D8A6", "15": "#BB3E03",
    "16": "#005F73", "17": "#AE2012", "18": "#9B2226", "19": "#E09F3E", "20": "#335C67",
    "21": "#540B0E", "POR_ASIGNAR": "#6D6D6D"
}

# --- 2. CARGA DEL CATÁLOGO (VERSIÓN OPTIMIZADA) ---
@st.cache_data
def cargar_catalogo_seguro():
    archivo = "catalogo_sonora.csv"
    if os.path.exists(archivo):
        try:
            # Intentamos leer con detección automática de separador y codificaciones comunes
            try:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
            except:
                df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
            
            # Limpiamos los nombres de las columnas para quitar espacios y poner todo en mayúsculas
            df.columns = df.columns.str.strip().str.upper()
            
            # Buscamos de forma más agresiva cualquier columna que se parezca a SECCION o DISTRITO
            col_seccion = None
            col_distrito = None
            
            for col in df.columns:
                if any(x in col for x in ['SEC', 'SECC', 'SECCION', 'SECCIÓN', 'NUM_SEC']):
                    col_seccion = col
                if any(x in col for x in ['DTO', 'DIST', 'DISTRITO', 'LOCAL']):
                    col_distrito = col

            if col_seccion and col_distrito:
                df[col_seccion] = df[col_seccion].astype(str).str.replace('.0', '', regex=False).str.strip()
                return df, col_seccion, col_distrito
            else:
                # Si las columnas tienen nombres raros, asignamos por posición como plan de respaldo
                if len(df.columns) >= 2:
                    columnas_nuevas = list(df.columns)
                    columnas_nuevas[0] = 'SECCION'
                    columnas_nuevas[1] = 'DISTRITO'
                    df.columns = columnas_nuevas
                    df['SECCION'] = df['SECCION'].astype(str).str.replace('.0', '', regex=False).str.strip()
                    return df, 'SECCION', 'DISTRITO'
                    
        except Exception as e:
            st.error(f"Error interno al procesar el catálogo: {e}")
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

# --- 4. CONTROL DE PESTAÑAS ---
tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 PANEL DE CONTROL", "📢 WHATSAPP"])

# --- PESTAÑA 1: CAPTURA ---
with tab1:
    col_campos, col_leyenda = st.columns([3, 1])
    with col_leyenda:
        st.subheader("📌 Distritos")
        for d, color in COLORES_DISTRITOS.items():
            if d.isdigit():
                st.markdown(f'<div style="display:flex;align-items:center;margin-bottom:3px;"><div style="width:12px;height:12px;background:{color};border-radius:50%;margin-right:8px;"></div><span style="font-size:12px; font-weight:500;">Dto {d}</span></div>', unsafe_allow_html=True)

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
                    "FOTO_PER": path_p, "FOTO_INE": path_i
                }])
                nuevo_reg.to_csv(base_file, mode='a', header=not os.path.exists(base_file), index=False)
                st.success("¡Registro Guardado Exitosamente!")
                st.balloons()
            else:
                st.warning("⚠️ Nombre y Celular son campos obligatorios.")

        st.markdown(f'<div style="border: 5px solid {color_res}; border-radius: 12px; overflow: hidden; margin-top:15px;">', unsafe_allow_html=True)
        url_mapa_libre = f"https://www.openstreetmap.org/export/embed.html?bbox=-111.05%2C29.03%2C-110.90%2C29.15&layer=mapnik"
        components.iframe(url_mapa_libre, height=400)
        st.markdown('</div>', unsafe_allow_html=True)

# --- PESTAÑA 2: PANEL DE CONTROL ---
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

# --- PESTAÑA 3: MODULO WHATSAPP ---
with tab3:
    st.header("📢 Módulo de Mensajería")
    base_file = "BASE_TOTAL_CONTACTOS.csv"
    
    if os.path.exists(base_file):
        try:
            df_w = pd.read_csv(base_file, on_bad_lines='skip', engine='python')
            mensaje_base = st.text_area("Mensaje a enviar (Usa {nombre} para personalizar):", "Hola {nombre}, un saludo.")
            
            c_f1, c_f2 = st.columns(2)
            distritos_disponibles = sorted([str(x) for x in df_w['DISTRITO'].unique() if pd.notna(x)])
            filtro_dto = c_f1.selectbox("Filtrar envío por Distrito Local:", ["TODOS"] + distritos_disponibles)
            
            contactos_filtrados = df_w if filtro_dto == "TODOS" else df_w[df_w['DISTRITO'].astype(str) == filtro_dto]
            
            # --- DETECCIÓN DE ENTORNO NUBE VS LOCAL ---
            if not PYWHATKIT_AVAILABLE or os.environ.get("STREAMLIT_SERVER_COOKIE_SECRET") is not None:
                st.info("🌐 **Modo Web Activo**: Generando enlaces directos de envío rápido para WhatsApp.")
                
                if not contactos_filtrados.empty:
                    for idx, row in contactos_filtrados.reset_index(drop=True).iterrows():
                        num = str(row['CELULAR']).strip().split('.')[0]
                        if not num.startswith('52'): 
                            num = '52' + num if not num.startswith('+52') else num.replace('+', '')
                        else:
                            if num.startswith('+52'): num = num.replace('+', '')
                        
                        msg_personalizado = mensaje_base.replace("{nombre}", str(row['NOMBRE']))
                        texto_url = urllib.parse.quote(msg_personalizado)
                        
                        url_wa = f"https://api.whatsapp.com/send?phone={num}&text={texto_url}"
                        
                        col_nom, col_btn = st.columns([3, 1])
                        col_nom.write(f"👤 **{row['NOMBRE']}** ({row['CELULAR']})")
                        col_btn.markdown(f'[@ Enviar por WhatsApp]({url_wa})', unsafe_allow_html=True)
                else:
                    st.warning("No hay contactos para el filtro seleccionado.")
            
            # Modo Local (Tu Windows)
            else:
                st.success("💻 **Modo Local Activo**: Automatización con simulación de mouse disponible.")
                if st.button("🚀 INICIAR ENVÍO AUTOMÁTICO MASIVO"):
                    if not contactos_filtrados.empty:
                        barra_progreso = st.progress(0)
                        total_envios = len(contactos_filtrados)
                        for idx, row in contactos_filtrados.reset_index(drop=True).iterrows():
                            try:
                                num = str(row['CELULAR']).strip().split('.')[0]
                                if not num.startswith('+52'): num = '+52' + num
                                msg_personalizado = mensaje_base.replace("{nombre}", str(row['NOMBRE']))
                                st.info(f"Enviando de forma automática a {row['NOMBRE']}...")
                                kit.sendwhatmsg_instantly(num, msg_personalizado, wait_time=12, tab_close=True)
                                time.sleep(4)
                            except Exception as err:
                                st.error(f"❌ Error al enviar a {row['NOMBRE']}: {err}")
                            barra_progreso.progress((idx + 1) / total_envios)
                        st.success("¡Envío masivo finalizado!")
                    else:
                        st.warning("No se encontraron registros activos.")
        except Exception as e:
            st.error(f"Error en el módulo de WhatsApp: {e}")
    else:
        st.warning("No hay registros disponibles para realizar envíos.")
