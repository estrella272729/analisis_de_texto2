import streamlit as st
import pandas as pd
from textblob import TextBlob
import re
import json

# ====== Traducción opcional (googletrans) ======
TRANSLATION_AVAILABLE = False
try:
    from googletrans import Translator
    translator = Translator()
    TRANSLATION_AVAILABLE = True
except Exception:
    translator = None

# ====== Lottie ======
from streamlit_lottie import st_lottie

# =======================
# Configuración de página
# =======================
st.set_page_config(
    page_title="Analizador de Texto Simple",
    page_icon="📊",
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

# Si tus JSON están en la misma carpeta que app.py:
LOTTIE_HAPPY = load_lottie_json("JFUBKdNqei.json")     # animación feliz
LOTTIE_SAD   = load_lottie_json("emojitriste.json")    # animación triste
# Si los tienes dentro de /assets, usa:
# LOTTIE_HAPPY = load_lottie_json("assets/JFUBKdNqei.json")
# LOTTIE_SAD   = load_lottie_json("assets/emojitriste.json")

POS_THRESHOLD = 0.05
NEG_THRESHOLD = -0.05

# Función para contar palabras sin depender de NLTK
def contar_palabras(texto):
    # Lista básica de palabras vacías en español e inglés
    stop_words = set([
        # Español
        "a","al","algo","algunas","algunos","ante","antes","como","con","contra","cual","cuando","de","del","desde",
        "donde","durante","e","el","ella","ellas","ellos","en","entre","era","eras","es","esa","esas","ese","eso",
        "esos","esta","estas","este","esto","estos","ha","había","han","has","hasta","he","la","las","le","les","lo",
        "los","me","mi","mía","mías","mío","míos","mis","mucho","muchos","muy","nada","ni","no","nos","nosotras",
        "nosotros","nuestra","nuestras","nuestro","nuestros","o","os","otra","otras","otro","otros","para","pero",
        "poco","por","porque","que","quien","quienes","qué","se","sea","sean","según","si","sido","sin","sobre","sois",
        "somos","son","soy","su","sus","suya","suyas","suyo","suyos","también","tanto","te","tenéis","tenemos","tener",
        "tengo","ti","tiene","tienen","todo","todos","tu","tus","tuya","tuyas","tuyo","tuyos","tú","un","una","uno",
        "unos","vosotras","vosotros","vuestra","vuestras","vuestro","vuestros","y","ya","yo",
        # Inglés
        "about","above","after","again","against","all","am","an","and","any","are","aren't","as","at","be","because",
        "been","before","being","below","between","both","but","by","can't","cannot","could","couldn't","did","didn't",
        "do","does","doesn't","doing","don't","down","during","each","few","for","from","further","had","hadn't",
        "has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself",
        "him","himself","his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's",
        "its","itself","let's","me","more","most","mustn't","my","myself","no","nor","not","of","off","on","once",
        "only","or","other","ought","our","ours","ourselves","out","over","own","same","shan't","she","she'd","she'll",
        "she's","should","shouldn't","so","some","such","than","that","that's","the","their","theirs","them",
        "themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those",
        "through","to","too","under","until","up","very","was","wasn't","we","we'd","we'll","we're","we've","were",
        "weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's",
        "with","would","wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"
    ])
    # Limpiar y tokenizar texto
    palabras = re.findall(r'\b\w+\b', texto.lower())
    # Filtrar palabras vacías y contar frecuencias
    palabras_filtradas = [palabra for palabra in palabras if palabra not in stop_words and len(palabra) > 2]
    # Contar frecuencias
    contador = {}
    for palabra in palabras_filtradas:
        contador[palabra] = contador.get(palabra, 0) + 1
    # Ordenar por frecuencia
    contador_ordenado = dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))
    return contador_ordenado, palabras_filtradas

# Función para traducir texto (opcional)
def traducir_texto(texto, usar_traduccion: bool):
    if usar_traduccion and TRANSLATION_AVAILABLE and translator is not None:
        try:
            traduccion = translator.translate(texto, src='auto', dest='en')
            return traduccion.text
        except Exception as e:
            st.sidebar.warning(f"No se pudo traducir (continuaré sin traducción): {e}")
    return texto  # Devolver el texto original si no se traduce

# Función para procesar el texto con TextBlob (con traducción opcional)
def procesar_texto(texto, usar_traduccion: bool):
    # Guardar el texto original
    texto_original = texto
    # Traducir (o no) el texto para análisis
    texto_analizado = traducir_texto(texto_original, usar_traduccion)
    # Analizar el texto con TextBlob
    blob = TextBlob(texto_analizado)
    sentimiento = blob.sentiment.polarity
    subjetividad = blob.sentiment.subjectivity
    # Extraer frases
    frases_originales = [f.strip() for f in re.split(r'[.!?]+', texto_original) if f.strip()]
    frases_analizadas = [f.strip() for f in re.split(r'[.!?]+', texto_analizado) if f.strip()]
    frases_combinadas = []
    for i in range(min(len(frases_originales), len(frases_analizadas))):
        frases_combinadas.append({
            "original": frases_originales[i],
            "analizado": frases_analizadas[i]
        })
    # Contar palabras (sobre el texto analizado)
    contador_palabras, palabras = contar_palabras(texto_analizado)
    return {
        "sentimiento": sentimiento,
        "subjetividad": subjetividad,
        "frases": frases_combinadas,
        "contador_palabras": contador_palabras,
        "palabras": palabras,
        "texto_original": texto_original,
        "texto_analizado": texto_analizado
    }

# Función para crear visualizaciones
def crear_visualizaciones(resultados):
    col1, col2 = st.columns(2)

    # Visualización de sentimiento y subjetividad con barras de progreso
    with col1:
        st.subheader("Análisis de Sentimiento y Subjetividad")

        # Normalizamos a porcentajes enteros (st.progress funciona mejor así)
        sentimiento_pct = int((resultados["sentimiento"] + 1) / 2 * 100)  # -1..1 -> 0..100
        subjetividad_pct = int(resultados["subjetividad"] * 100)          # 0..1  -> 0..100

        st.write("**Sentimiento (0=negativo, 100=positivo):**")
        st.progress(sentimiento_pct)

        # Mensaje + animación según el sentimiento
        if resultados["sentimiento"] > POS_THRESHOLD:
            st.success(f"📈 Positivo ({resultados['sentimiento']:.2f})")
            if LOTTIE_HAPPY:
                st_lottie(LOTTIE_HAPPY, height=220, loop=True, key="happy")
        elif resultados["sentimiento"] < NEG_THRESHOLD:
            st.error(f"📉 Negativo ({resultados['sentimiento']:.2f})")
            if LOTTIE_SAD:
                st_lottie(LOTTIE_SAD, height=220, loop=True, key="sad")
        else:
            st.info(f"📊 Neutral ({resultados['sentimiento']:.2f})")

        st.write("**Subjetividad (0=objetivo, 100=subjetivo):**")
        st.progress(subjetividad_pct)

        if resultados["subjetividad"] > 0.5:
            st.warning(f"💭 Alta subjetividad ({resultados['subjetividad']:.2f})")
        else:
            st.info(f"📋 Baja subjetividad ({resultados['subjetividad']:.2f})")

    # Palabras más frecuentes usando chart de Streamlit
    with col2:
        st.subheader("Palabras más frecuentes")
        if resultados["contador_palabras"]:
            palabras_top = list(resultados["contador_palabras"].items())[:10]
            df_top = pd.DataFrame(palabras_top, columns=["palabra", "frecuencia"]).set_index("palabra")
            st.bar_chart(df_top)
        else:
            st.write("No hay suficientes palabras para graficar.")

    # Mostrar texto analizado
    st.subheader("Texto Analizado")
    with st.expander("Ver texto original vs analizado"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Texto Original (Español):**")
            st.text(resultados["texto_original"])
        with c2:
            st.markdown("**Texto Analizado (posible traducción):**")
            st.text(resultados["texto_analizado"])

    # Análisis de frases
    st.subheader("Frases detectadas")
    if resultados["frases"]:
        for i, frase_dict in enumerate(resultados["frases"][:10], 1):
            frase_original = frase_dict["original"]
            frase_analizada = frase_dict["analizado"]
            try:
                s = TextBlob(frase_analizada).sentiment.polarity
                emoji = "😊" if s > POS_THRESHOLD else ("😟" if s < NEG_THRESHOLD else "😐")
                st.write(f"{i}. {emoji} **Original:** *\"{frase_original}\"*")
                st.write(f"   **Análisis:** *\"{frase_analizada}\"* (Sentimiento: {s:.2f})")
                st.write("---")
            except Exception:
                st.write(f"{i}. **Original:** *\"{frase_original}\"*")
                st.write(f"   **Análisis:** *\"{frase_analizada}\"*")
                st.write("---")
    else:
        st.write("No se detectaron frases.")

# =======================
# UI
# =======================
st.title("📝 Analizador de Texto con TextBlob")
st.markdown("""
Esta aplicación utiliza TextBlob para análisis básico:
- **Sentimiento** y **subjetividad**
- **Palabras clave** y **frecuencia**
- **Frases** con mini-sentimiento
""")

# Barra lateral
st.sidebar.title("Opciones")
modo = st.sidebar.selectbox("Selecciona el modo de entrada:", ["Texto directo", "Archivo de texto"])

usar_traduccion = st.sidebar.checkbox(
    "Traducir automáticamente al inglés (mejora el análisis de sentimiento)",
    value=True if TRANSLATION_AVAILABLE else False,
    help="Usa googletrans si está disponible. Si no, se analiza el texto tal cual."
)

# Lógica principal según el modo seleccionado
if modo == "Texto directo":
    st.subheader("Ingresa tu texto para analizar")
    texto = st.text_area("", height=200, placeholder="Escribe o pega aquí el texto que deseas analizar...")
    if st.button("Analizar texto"):
        if texto.strip():
            with st.spinner("Analizando texto..."):
                resultados = procesar_texto(texto, usar_traduccion)
                crear_visualizaciones(resultados)
        else:
            st.warning("Por favor, ingresa algún texto para analizar.")

elif modo == "Archivo de texto":
    st.subheader("Carga un archivo de texto")
    archivo = st.file_uploader("", type=["txt", "csv", "md"])
    if archivo is not None:
        try:
            contenido = archivo.getvalue().decode("utf-8", errors="ignore")
            with st.expander("Ver contenido del archivo"):
                st.text(contenido[:1000] + ("..." if len(contenido) > 1000 else ""))
            if st.button("Analizar archivo"):
                with st.spinner("Analizando archivo..."):
                    resultados = procesar_texto(contenido, usar_traduccion)
                    crear_visualizaciones(resultados)
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# Información adicional
with st.expander("📚 Información sobre el análisis"):
    st.markdown("""
- **Sentimiento**: −1 (muy negativo) a 1 (muy positivo)
- **Subjetividad**: 0 (objetivo) a 1 (subjetivo)
- La **traducción** es opcional; si falla o no está instalada, se analiza el texto original.
""")

# Pie de página
st.markdown("---")
st.markdown("Desarrollado con ❤️ usando Streamlit, TextBlob y Lottie")

