import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Konfiguracja sesji i interfejsu
st.set_page_config(
    page_title="System Analizy Przepustowości Kolejek", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Inicjalizacja połączenia z bazą danych Supabase
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Błąd inicjalizacji połączenia z bazą danych: {e}")
    st.stop()

# Pobieranie danych telemetrycznych
def fetch_telemetry_data():
    try:
        response = supabase.table("queue_data").select("*").order("created_at", desc=True).limit(100).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Błąd pobierania danych z serwera: {e}")
        return pd.DataFrame()

# Nagłówek systemu
st.title("Panel Analityczny Przepustowości Stanowisk")
st.caption("System monitorowania obciążenia punktów obsługi w oparciu o architekturę sensorów odległościowych i ruchu.")

# Panel kontrolny
col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("Odśwież dane systemowe", use_container_width=True):
        st.rerun()

# Pobranie i weryfikacja danych
df = fetch_telemetry_data()

if not df.empty:
    # Konwersja znaczników czasu
    df['created_at'] = pd.to_datetime(df['created_at'])
    latest_event = df.iloc[0]
    
    st.subheader("Status operacyjny (Ostatnie zdarzenie rejestrowane na wyjściu)")
    
    # Sekcja metryk głównych
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric(
            label="Stanowisko Obsługi (Pozycja 1)",
            value="Zajęte" if latest_event['miejsce2'] else "Wolne",
            delta="Detekcja obiektu" if latest_event['miejsce2'] else "Brak obiektu",
            delta_color="normal" if latest_event['miejsce2'] else "off"
        )
        
    with metric_col2:
        st.metric(
            label="Bufor Kolejki (Pozycja 5)",
            value="Wykryto zator" if latest_event['miejsce1'] else "Norma",
            delta="Przekroczono limit długości" if latest_event['miejsce1'] else "Optymalna przepustowość",
            delta_color="inverse" if latest_event['miejsce1'] else "normal"
        )
        
    with metric_col3:
        st.metric(
            label="Czas ostatniego cyklu obsługi",
            value=f"{latest_event['czas_sekundy']} s",
            delta="Dane z sensora wyjściowego"
        )

    st.subheader("Architektura rozmieszczenia sensorów i stan sekcji")
    
    # Wizualizacja przestrzenna oparta na statusach komponentów
    zone1, zone2, zone3, zone4, zone5, zone_exit = st.columns(6)
    
    with zone1:
        st.markdown("**Pozycja 1 (Okienko)**")
        if latest_event['miejsce2']:
            st.error("Status: Aktywny")
        else:
            st.success("Status: Pusty")
        st.caption("Sensor odległości nr 1")
        
    with zone2:
        st.markdown("**Pozycja 2**")
        st.info("Strefa tranzytowa")
        
    with zone3:
        st.markdown("**Pozycja 3**")
        st.info("Strefa tranzytowa")
        
    with zone4:
        st.markdown("**Pozycja 4**")
        st.info("Strefa tranzytowa")
        
    with zone5:
        st.markdown("**Pozycja 5 (Ogon)**")
        if latest_event['miejsce1']:
            st.error("Status: Przepełnienie")
        else:
            st.success("Status: Norma")
        st.caption("Sensor odległości nr 2")
        
    with zone_exit:
        st.markdown("**Brama wyjściowa**")
        st.warning("Rejestrator logów")
        st.caption("Sensor ruchu PIR")

    st.divider()

    # Sekcja analizy wykresów
    chart_col1, chart_col2 = st.columns([3, 2])
    
    with chart_col1:
        st.subheader("Wykres dystrybucji czasu obsługi")
        
        # Profesjonalny wykres punktowy z linią trendu
        fig = px.scatter(
            df, 
            x='created_at', 
            y='czas_sekundy', 
            color='miejsce1',
            labels={
                'czas_sekundy': 'Czas operacyjny (sekundy)', 
                'created_at': 'Znacznik czasu zdarzenia', 
                'miejsce1': 'Wystąpienie zatoru w kolejce'
            },
            color_discrete_map={True: '#EF4444', False: '#10B981'},
            template="plotly_white"
        )
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with chart_col2:
        st.subheader("Dziennik zdarzeń systemowych")
        
        # Przygotowanie czytelnej tabeli danych
        log_df = df[['created_at', 'miejsce2', 'miejsce1', 'czas_sekundy']].copy()
        log_df.columns = ['Data i godzina', 'Stanowisko (Poz. 1)', 'Zator (Poz. 5)', 'Czas obsługi (s)']
        
        st.dataframe(
            log_df, 
            use_container_width=True, 
            hide_index=True
        )

else:
    st.info("Brak zarejestrowanych danych w systemie. Oczekiwanie na sygnał z sensora wyjściowego.")
