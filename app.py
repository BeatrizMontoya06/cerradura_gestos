import paho.mqtt.client as paho
import time
import json
import streamlit as st
import cv2
import numpy as np
import random
from PIL import Image as Image, ImageOps as ImagOps
from keras.models import load_model

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA (ESTILO CYBER SPACE / BEATRIZ'S HIVE - 2000s)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Bea's Smart Lock 🐝", 
    page_icon="🔒", 
    layout="wide"
)

# Estilo visual oscuro con acentos neón Y2K y tarjetas retro
st.markdown("""
    <style>
    .stApp {
        background-color: #0b0714;
        background-image: radial-gradient(#251a3a 1px, transparent 1px);
        background-size: 20px 20px;
        color: #d1c4e9;
        font-family: 'Courier New', Courier, monospace;
    }
    .top-marquee {
        background-color: #ffcc00;
        color: #1a0826;
        padding: 8px 15px;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        border: 2px dashed #ff007f;
        border-radius: 4px;
        margin-bottom: 20px;
        box-shadow: 0px 0px 10px rgba(255, 204, 0, 0.4);
    }
    .main-title {
        text-align: center;
        color: #ffaa00 !important;
        font-family: 'Courier New', Courier, monospace;
        font-size: 34px;
        font-weight: bold;
        text-shadow: 2px 2px #ff007f, 0px 0px 10px rgba(255, 170, 0, 0.6);
        margin-bottom: 25px;
    }
    h2, h3 {
        color: #ffaa00 !important;
        font-family: 'Courier New', Courier, monospace;
        text-shadow: 1px 1px #ff007f;
    }
    .cyber-card {
        background-color: #140d24;
        border: 2px solid #ff007f;
        border-radius: 6px;
        padding: 20px;
        margin-bottom: 25px;
        box-shadow: 4px 4px 0px #7b1fa2;
    }
    a {
        color: #00e5ff !important;
        text-decoration: none;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BARRA SUPERIOR Y TÍTULO
# -----------------------------------------------------------------------------
st.markdown("""
    <div class="top-marquee">
        🔒 Sistema de Seguridad Ciberfísico ✦ Reconocimiento Biométrico por IA ✦ Protocolo MQTT Activo 🚀
    </div>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>✨ * Cerradura Inteligente (Smart Lock) * ✨</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN MQTT Y MODELO
# -----------------------------------------------------------------------------
broker = "broker.hivemq.com"
port = 1883

def on_publish(client, userdata, result):
    print("El dato ha sido publicado \n")

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

# Inicializar modelo de IA (con caché para optimizar rendimiento en Streamlit)
@st.cache_resource
def load_ai_model():
    return load_model('keras_model.h5')

try:
    model = load_ai_model()
except Exception as e:
    st.error(f"⚠️ Error al cargar el modelo 'keras_model.h5': {e}")

# -----------------------------------------------------------------------------
# DISTRIBUCIÓN DE LA INTERFAZ EN DOS COLUMNAS
# -----------------------------------------------------------------------------
col_cam, col_panel = st.columns([1, 1], gap="medium")

with col_cam:
    st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
    st.subheader("📷 Panel de Captura Biométrica")
    st.write("Colócate frente a la cámara y toma una foto para validar el acceso:")
    
    img_file_buffer = st.camera_input("Toma una Foto")
    st.markdown('</div>', unsafe_allow_html=True)

with col_panel:
    st.markdown('<div class="cyber-card">', unsafe_allow_html=True)
    st.subheader("⚙️ Estado del Sistema y MQTT")
    st.write(f"**Broker:** `{broker}:{port}`")
    st.write(f"**Tópico de Salida:** `IMIA`")
    
    status_placeholder = st.empty()
    status_placeholder.info("⏳ En espera de captura fotográfica...")
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# PROCESAMIENTO DE LA IMAGEN E INFERENCIA
# -----------------------------------------------------------------------------
if img_file_buffer is not None:
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    img = Image.open(img_file_buffer)

    newsize = (224, 224)
    img = img.resize(newsize)
    img_array = np.array(img)

    # Normalizar la imagen para el modelo Keras
    normalized_image_array = (img_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array

    # Ejecutar inferencia
    prediction = model.predict(data)
    
    # Conexión MQTT robusta con ID aleatorio único
    try:
        client_id_mqtt = f"lock_client_{random.randint(1000, 9999)}"
        client1 = paho.Client(client_id=client_id_mqtt, protocol=paho.MQTTv311)
        client1.on_message = on_message
        client1.on_publish = on_publish
        client1.connect(broker, port)
    except Exception as err:
        st.error(f"Error de conexión al broker MQTT: {err}")

    with col_panel:
        if prediction[0][0] > 0.3:
            status_placeholder.success("🟢 ¡Acceso Autorizado! ➔ ABRIENDO CERRADURA")
            try:
                client1.publish("IMIA", '{"gesto": "Abre"}', qos=0, retain=False)
                client1.disconnect()
            except:
                pass
            time.sleep(0.2)
            
        elif prediction[0][1] > 0.3:
            status_placeholder.warning("🔴 Gesto de Cierre ➔ CERRANDO CERRADURA")
            try:
                client1.publish("IMIA", '{"gesto": "Cierra"}', qos=0, retain=False)
                client1.disconnect()
            except:
                pass
            time.sleep(0.2)
        else:
            status_placeholder.info("🟡 Imagen procesada. Gestos por debajo del umbral de confianza.")

# Pie de página
st.markdown("---")
st.markdown("""
    <p style='text-align: center; color: #ff007f; font-family: "Courier New", Courier, monospace; font-size: 12px;'>
        [:: SMART LOCK SYSTEM • 2000S RETRO VIBES • MQTT IOT INTEGRATION ::]
    </p>
""", unsafe_allow_html=True)
