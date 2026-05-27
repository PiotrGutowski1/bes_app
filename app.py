import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor Kolejki 1-5", layout="wide", page_icon="📏")

# Inicjalizacja Supabase
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# Pobieranie danych
def get_data():
    response = supabase.table("queue_data").select("*").order("created_at", desc=True).limit(100).execute()
    return pd.DataFrame(response.data)

# --- INTERFEJS ---
st.title("🕒 Monitor Przepustowości Kolejki (Poz. 1 & 5)")
st.markdown("Monitorowanie zajętości okienka (**Poz. 1**) oraz końca kolejki (**Poz. 5**).")

df = get_data()

if not df.empty:
    latest = df.iloc[0]
    
    # GŁÓWNE WSKAŹNIKI
    m1, m2, m3 = st.columns(3)
    
    with m1:
        # CZUJNIK 2 -> MIEJSCE 1 (Przy okienku)
        st.metric("Stan: Przy Okienku (Poz. 1)", 
                  "ZAJĘTE" if latest['miejsce2'] else "WOLNE",
                  delta="Obsługa w toku" if latest['miejsce2'] else "Oczekiwanie",
                  delta_color="normal" if latest['miejsce2'] else "inverse")
        
    with m2:
        # CZUJNIK 1 -> MIEJSCE 5 (Koniec kolejki)
        st.metric("Stan: Koniec Kolejki (Poz. 5)", 
                  "DŁUGA" if latest['miejsce1'] else "KRÓTKA",
                  delta="Wymagana pomoc" if latest['miejsce1'] else "Stabilnie",
                  delta_color="inverse" if latest['miejsce1'] else "normal")
        
    with m3:
        avg_wait = df['czas_sekundy'].mean()
        st.metric("Średni czas w kolejce", f"{avg_wait:.0f} s")

    st.divider()

    # WIZUALIZACJA KOLEJKI
    st.subheader("📍 Podgląd Przestrzenny")
    q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns(5)
    
    # Poz 1 (Czujnik 2)
    q_col1.info("👤 **Poz. 1**" if latest['miejsce2'] else "⚪ Poz. 1")
    q_col1.caption("Przy okienku")
    
    # Poz 2-4 (Symulacja/Puste)
    q_col2.text("---")
    q_col3.text("---")
    q_col4.text("---")
    
    # Poz 5 (Czujnik 1)
    q_col5.error("👤 **Poz. 5**" if latest['miejsce1'] else "⚪ Poz. 5")
    q_col5.caption("Koniec kolejki")

    # HISTORIA
    st.plotly_chart(px.line(df, x='created_at', y='czas_sekundy', title="Czas obsługi w czasie"), use_container_width=True)

else:
    st.warning("Czekam na dane z sensorów...")
