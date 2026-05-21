import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Konfiguracja strony
st.set_page_config(page_title="Monitor Kolejki TTN + Supabase", layout="wide")
st.title("📊 Panel Monitorowania Kolejki (Supabase)")

# 1. Inicjalizacja klienta Supabase z wykorzystaniem Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

try:
    supabase = init_supabase()
    
    # Przycisk do ręcznego odświeżania danych
    if st.button("🔄 Odśwież dane"):
        st.rerun()

    # 2. Pobieranie danych z tabeli Supabase
    # Zmień "pomiary_kolejki" na dokładną nazwę Twojej tabeli w Supabase
    # .order("created_at", desc=True) sortuje od najnowszych wpisów
    # .limit(100) pobiera ostatnie 100 rekordów, żeby nie przeciążać strony
    response = supabase.table("queue_data").select("*").order("created_at", desc=True).limit(100).execute()
    
    # Konwersja wyniku na Pandas DataFrame
    data = response.data
    
    if data:
        df = pd.DataFrame(data)
        
        # Tworzenie układu dwukolumnowego w Streamlit
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Ostatnie zdarzenia w kolejce")
            # Wyświetlamy ładną tabelę
            st.dataframe(df, use_container_width=True)
            
        with col2:
            st.subheader("Aktualny stan systemu")
            
            # Zakładamy przykładowe kolumny: 'at_window' (czy ktoś stoi przy okienku) 
            # oraz 'time_in_queue_sec' (czas spędzony w kolejce)
            if 'at_window' in df.columns:
                current_status = "ZAJĘTE" if df['at_window'].iloc[0] == True else "WOLNE"
                st.image("https://img.icons8.com/color/96/user.png" if current_status == "ZAJĘTE" else "https://img.icons8.com/color/96/empty-box.png", width=60)
                st.metric(label="Okienko obsługi", value=current_status)
                
            if 'time_in_queue_sec' in df.columns:
                avg_time = df['time_in_queue_sec'].mean()
                st.metric(label="Średni czas w kolejce", value=f"{int(avg_time)} sek")
                
    else:
        st.info("Połączono z Supabase, ale tabela jest pusta. Czekam na pierwsze dane z The Things Network!")

except Exception as e:
    st.error(f"Błąd podczas połączenia z Supabase: {e}")
    st.info("Sprawdź czy URL oraz API Key w sekretach są poprawne oraz czy nazwa tabeli w kodzie się zgadza.")
