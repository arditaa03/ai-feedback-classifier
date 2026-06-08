import streamlit as st
import pandas as pd
from groq import Groq
import json

# 1. Konfigurimi i Groq (Zëvendësoje me API Key tënd të pastër)
api_key = os.environ.get("GROQ_API_KEY") 
client = Groq(api_key=api_key)

def analizo_feedbackun(teksti):
    """Përdor modelin Llama 3 përmes Groq për analizë shumëgjuhëshe (Shqip, English, Deutsch)."""
    prompt = f"""
    Ti je një asistent AI për analizën e të dhënave të biznesit në një mjedis ndërkombëtar.
    Analizo tekstin e mëposhtëm që përfaqëson një email ose feedback nga klienti.
    
    UDHËZIME TË RËNDËSISHME PËR GJUHËN:
    1. Detekto gjuhën e tekstit të klientit (Shqip, English, apo Deutsch).
    2. Përmbledhja ("përmbledhja") dhe Kategoria ("kategoria") DUHET të kthehen në të njëjtën gjuhë si teksti origjinal!
    
    Përkthimi i kategorive sipas gjuhës:
    - Nëse është Shqip: "Ankesë", "Kërkesë për Çmim", "Lëvdatë", "Mbështetje Teknike"
    - Nëse është English: "Complaint", "Pricing Request", "Praise", "Technical Support"
    - Nëse është Deutsch: "Beschwerde", "Preisanfrage", "Lob", "Technischer Support"

    Nxjerr këto informacione në formatin e pastër JSON:
    1. "gjuha": (Shqip, English, ose Deutsch)
    2. "kategoria": (Kategoria e përshtatur në gjuhën përkatëse sipas listës më lart)
    3. "sentimenti": (Pozitiv, Neutral, Negativ) - këtë mbaje në Shqip për menaxhmentin lokal
    4. "urgjenca": (E lartë, Mesatare, E ulët) - këtë mbaje në Shqip për menaxhmentin lokal
    5. "përmbledhja": Një fjali e shkurtër në gjuhën e klientit që përmbledh kërkesën.

    Teksti për analizë:
    "{teksti}"
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "gjuha": "Gabim", 
            "kategoria": "Gabim", 
            "sentimenti": "Gabim", 
            "urgjenca": "Gabim", 
            "përmbledhja": str(e)
        }

# 2. Ndërtimi i UI me Streamlit
st.set_page_config(page_title="AI Feedback Classifier", layout="wide")
st.title("📊 AI Customer Feedback & Lead Categorizer (Multilingual)")
st.write("Ky projekt demonstron automatizimin e proceseve të biznesit përmes LLM-ve për tregun Gjerman, Anglez dhe Shqiptar.")

# Inicializimi i tabelës me kolonën e re "Gjuha"
if "df_baza" not in st.session_state:
    st.session_state.df_baza = pd.DataFrame(columns=["Teksti Origjinal", "Gjuha", "Kategoria", "Sentimenti", "Urgjenca", "Përmbledhja"])

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Inputi nga Klienti")
    user_input = st.text_area(
        "Shkruaj një email ose feedback (Shqip, English, Deutsch):",
        height=150,
        placeholder="Shkruaj ose ngjit tekstin këtu..."
    )
    
    if st.button("Analizo me AI ✨", use_container_width=True):
        if user_input.strip() != "":
            with st.spinner("Duke procesuar me Groq AI..."):
                rezultati = analizo_feedbackun(user_input)
                
                # Ruajtja e të dhënave duke përfshirë edhe gjuhën
                new_row = {
                    "Teksti Origjinal": user_input,
                    "Gjuha": rezultati.get("gjuha"),
                    "Kategoria": rezultati.get("kategoria"),
                    "Sentimenti": rezultati.get("sentimenti"),
                    "Urgjenca": rezultati.get("urgjenca"),
                    "Përmbledhja": rezultati.get("përmbledhja")
                }
                
                st.session_state.df_baza = pd.concat([st.session_state.df_baza, pd.DataFrame([new_row])], ignore_index=True)
                st.success("U analizua me sukses!")
        else:
            st.warning("Ju lutem shkruani diçka para se të klikoni butonin.")

with col2:
    st.subheader("Rezultatet e Fundit nga AI")
    if not st.session_state.df_baza.empty:
        fund = st.session_state.df_baza.iloc[-1]
        st.json({
            "Gjuha e Detektuar": fund["Gjuha"],
            "Kategoria": fund["Kategoria"],
            "Sentimenti": fund["Sentimenti"],
            "Urgjenca": fund["Urgjenca"],
            "Përmbledhja": fund["Përmbledhja"]
        })
    else:
        st.info("Asnjë të dhënë e analizuar ende.")

st.subheader("📋 Tabela e të Dhënave të Automatizuara (Gati për CRM / Excel)")
st.dataframe(st.session_state.df_baza, use_container_width=True)

if not st.session_state.df_baza.empty:
    csv = st.session_state.df_baza.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Shkarko tabelën si CSV", 
        data=csv, 
        file_name='feedback_analizuar.csv', 
        mime='text/csv'
    )