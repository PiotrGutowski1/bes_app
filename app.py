import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# --- KONFIGURACJA ---
st.set_page_config(page_title="Smart Queue Monitor", layout="wide", page_icon="🕒")

# Stylizacja UI (Dark Mode)
st.markdown("""
    <style>
    .status-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; }
    .occupied { background-color: #ff4b4b; color: white; }
    .free { background-color: #28a745; color: white; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# --- LOGIKA POBIERANIA DANYCH ---
def get_data():
    # Pobieramy 100 ostatnich wpisów
    response = supabase.table("queue_data").select("*").order("created_at", desc=True).limit(100).execute()
    return pd.DataFrame(response.data)

# --- UI ---
st.title("🕒 Monitor Stanu Kolejki LoRaWAN")
st.info("System monitoruje wejście (Miejsce 1) oraz stanowisko obsługi (Miejsce 2).")

if st.button("🔄 Odśwież Dane"):
    st.rerun()

df = get_data()

if not df.empty:
    # 1. WIDOK AKTUALNY (Ostatni rekord)
    latest = df.iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status1 = "ZAJĘTE" if latest['miejsce1'] else "WOLNE"
        st.markdown(f"### Wejście (PIR 1)")
        st.markdown(f'<div class="status-box {"occupied" if latest["miejsce1"] else "free"}">{status1}</div>', unsafe_allow_html=True)
        
    with col2:
        status2 = "ZAJĘTE" if latest['miejsce2'] else "WOLNE"
        st.markdown(f"### Przy Okienku (PIR 2)")
        st.markdown(f'<div class="status-box {"occupied" if latest["miejsce2"] else "free"}">{status2}</div>', unsafe_allow_html=True)
        
    with col3:
        avg_wait = df['czas_sekundy'].mean()
        st.metric("Średni czas czekania", f"{avg_wait:.1f} s", delta_color="inverse")

    st.divider()

    # 2. WYKRES TRENDÓW
    st.subheader("📈 Historia Czasu Oczekiwania")
    # Konwersja czasu na czytelny format
    df['created_at'] = pd.to_datetime(df['created_at'])
    fig = px.area(df, x="created_at", y="czas_sekundy", 
                  title="Czas spędzony w kolejce (sekundy)",
                  labels={"created_at": "Czas zdarzenia", "czas_sekundy": "Sekundy"},
                  color_discrete_sequence=['#deff9a'])
    fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

    # 3. TABELA LOGÓW
    st.subheader("📋 Ostatnie Logi Systemowe")
    st.dataframe(df[['created_at', 'device_id', 'miejsce1', 'miejsce2', 'czas_sekundy']], use_container_width=True)

else:
    st.warning("Brak danych w tabeli queue_data. Upewnij się, że urządzenie wysyła dane.")
