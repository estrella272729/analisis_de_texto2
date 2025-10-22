import streamlit as st
import pandas as pd
from textblob import TextBlob
import re
import json
from streamlit_lottie import st_lottie

# ====== Traducción opcional (googletrans) ======
TRANSLATION_AVAILABLE = False
try:
    from googletrans import Translator
    translator = Translator()
    TRANSLATION_AVAILABLE = True
except Exception:
    translator = None

# =======================
# Configuración de página
# =======================
st.set_page_config(
    page_title="Analizador de Sentimientos: ¿No sabes cómo te sientes? Cuéntanos y te ayudamos.",
    page_icon="💬",
    layout="wide"
)

# =======================
# Utilidades
# =======================
def load_lottie_json(path: str):
    """Carga un archivo .json de Lottie desde disco."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"No pude cargar la animación: {path} ({e})")
        return None

# Animaciones
LOTTIE_HAPPY = load_lottie_json("laughing cat.json")
LOTTIE_SAD   = load_lottie_json("Sad Star.json")

# =======================
# Umbrales
# =======================
POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05

# =======================
# Funciones auxiliares
# =======================
def contar_palabras(texto):
    palabras = re.findall(r'\b\w+\b', texto.lower())
    contador = {}
    for palabra in palabras:
        if len(palabra) > 2:
            contador[palabra] = contador.get(palabra, 0) + 1
    contador_ordenado = dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))
    return contador_ordenado, palabras

def traducir_texto(texto, usar_traduccion: bool):
    if usar_traduccion and TRANSLATION_AVAILABLE and translator is not None:
        try:
            traduccion = translator.translate(texto, src='auto', dest='en')
            return traduccion.text
        except Exception as e:
            st.sidebar.warning(f"No se pudo traducir: {e}")
    return texto

def procesar_texto(texto, usar_traduccion: bool):
    texto_original = texto
    texto_analizado = traducir_texto(texto_original, usar_traduccion)
    blob = TextBlob(texto_analizado)
    sentimiento = blob.sentiment.polarity
    subjetividad = blob.sentiment.subjectivity
    frases = [f.strip() for f in re.split(r'[.!?]+', texto_original) if f.strip()]
    contador_palabras, palabras = contar_palabras(texto_analizado)
    return {
        "sentimiento": sentimiento,
        "subjetividad": subjetividad,
        "frases": frases,
        "contador_palabras": contador_palabras,
        "texto_original": texto_original,
        "texto_analizado": texto_analizado
    }

# =======================
# Interfaz - Analizador de Sentimientos 💬
# =======================
st.markdown("""
<div style='text-align:center'>
    <h1 style='color:#4C6EF5;'> Analizador de Sentimientos</h1>
    <h3 style='color:#6C757D;'>¿No sabes cómo te sientes? Cuéntanos y te ayudamos a entenderlo.</h3>
</div>
""", unsafe_allow_html=True)

st.markdown("""
A veces es difícil poner en palabras lo que sentimos.  
Escribe tus pensamientos, una reflexión o lo que tengas en mente,  
y te ayudaremos a descubrir el **tono emocional** detrás de tus palabras   
""")

st.sidebar.title("⚙️ Opciones de Análisis")
modo = st.sidebar.radio("Selecciona el modo de entrada:", ["Texto directo", "Archivo de texto"])
usar_traduccion = st.sidebar.checkbox("Traducir al inglés (mejora el análisis)", value=True)

# =======================
# Entrada de texto
# =======================
if modo == "Texto directo":
    st.subheader(" Cuéntanos cómo te sientes:")
    texto = st.text_area("", height=200, placeholder="Escribe aquí lo que piensas o sientes...")
    if st.button("Analizar "):
        if texto.strip():
            with st.spinner("Analizando tus palabras... "):
                resultados = procesar_texto(texto, usar_traduccion)
                sentimiento = resultados["sentimiento"]
                subjetividad = resultados["subjetividad"]

                st.write("###  Resultado emocional:")
                if sentimiento > POS_THRESHOLD:
                    st.success(f"Tu texto refleja una **energía positiva** ({sentimiento:.2f}) 🌼")
                    if LOTTIE_HAPPY: st_lottie(LOTTIE_HAPPY, height=200)
                elif sentimiento < NEG_THRESHOLD:
                    st.error(f"Tu texto tiene un tono **triste o melancólico** ({sentimiento:.2f}) 🌧️")
                    if LOTTIE_SAD: st_lottie(LOTTIE_SAD, height=200)
                else:
                    st.info(f"Tu texto parece **neutral o equilibrado** ({sentimiento:.2f}) 🌗")

                st.write(f"**Subjetividad (nivel de opinión personal):** {subjetividad:.2f}")
                st.write("---")
                st.write("**Palabras más frecuentes:**")
                df = pd.DataFrame(list(resultados["contador_palabras"].items())[:10], columns=["Palabra", "Frecuencia"])
                st.bar_chart(df.set_index("Palabra"))
        else:
            st.warning("Por favor, escribe algo para analizar 📝")

else:
    st.subheader(" Carga un archivo de texto para analizar")
    archivo = st.file_uploader("", type=["txt", "csv", "md"])
    if archivo:
        contenido = archivo.getvalue().decode("utf-8", errors="ignore")
        st.text_area("Vista previa:", contenido[:1000])
        if st.button("Analizar archivo "):
            with st.spinner("Analizando tu archivo..."):
                resultados = procesar_texto(contenido, usar_traduccion)
                st.success("¡Análisis completado! ")
                st.bar_chart(pd.DataFrame(list(resultados["contador_palabras"].items())[:10],
                                          columns=["Palabra", "Frecuencia"]).set_index("Palabra"))

