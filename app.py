import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Monitor Kolejki", layout="wide")

# Połączenie z Supabase
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Błąd połączenia z bazą: {e}")
    st.stop()

# Pobieranie danych
def fetch_data():
    try:
        response = supabase.table("queue_data").select("*").order("created_at", desc=True).limit(100).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return pd.DataFrame()

# Nagłówek aplikacji
st.title("Monitor Kolejki")

if st.button("Odśwież dane"):
    st.rerun()

df = fetch_data()

if not df.empty:
    # Konwersja na typ datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # POPRAWKA STREFY CZASOWEJ: Dodanie 2 godzin do timestampu
    df['created_at'] = df['created_at'] + pd.Timedelta(hours=2)
    
    latest = df.iloc[0]
    
    # Obliczanie średniego czasu obsługi
    avg_time = df['czas_sekundy'].mean()
    
    # Główne wskaźniki
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.metric(
            label="Miejsce 1 (Okienko)",
            value="Zajęte" if latest['miejsce2'] else "Wolne"
        )
        
    with m2:
        st.metric(
            label="Miejsce 5 (Koniec kolejki)",
            value="Zajęte" if latest['miejsce1'] else "Wolne"
        )
        
    with m3:
        st.metric(
            label="Ostatni czas obsługi",
            value=f"{latest['czas_sekundy']} s"
        )
        
    with m4:
        st.metric(
            label="Średni czas obsługi",
            value=f"{avg_time:.1f} s"
        )

    st.divider()

    # Stan czujników
    st.subheader("Aktualny stan czujników")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Czujnik odległości 1 (Okienko)**")
        if latest['miejsce2']:
            st.error("Wykryto obecność")
        else:
            st.success("Brak obecności")
        
    with c2:
        st.markdown("**Czujnik odległości 2 (Koniec kolejki)**")
        if latest['miejsce1']:
            st.error("Wykryto obecność")
        else:
            st.success("Brak obecności")
        
    with c3:
        st.markdown("**Czujnik PIR (Wyjście)**")
        st.info("Oczekiwanie na impuls wyjścia")

    st.divider()

    # Wykres i tabela (Obydwa elementy korzystają z poprawionej kolumny 'created_at')
    chart_col, table_col = st.columns([3, 2])
    
    with chart_col:
        st.subheader("Czas obsługi kolejnych osób")
        fig = px.scatter(
            df, 
            x='created_at', 
            y='czas_sekundy', 
            color='miejsce1',
            labels={
                'czas_sekundy': 'Czas (sekundy)', 
                'created_at': 'Czas zdarzenia', 
                'miejsce1': 'Zajęte miejsce 5'
            },
            color_discrete_map={True: '#EF4444', False: '#10B981'},
            template="plotly_white"
        )
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with table_col:
        st.subheader("Ostatnie wpisy w bazie")
        log_df = df[['created_at', 'miejsce2', 'miejsce1', 'czas_sekundy']].copy()
        
        # Formatowanie wyświetlania daty i godziny w tabeli do czytelnego formatu (RRRR-MM-DD GG:MM:SS)
        log_df['created_at'] = log_df['created_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        log_df.columns = ['Czas', 'Miejsce 1', 'Miejsce 5', 'Czas (s)']
        st.dataframe(log_df, use_container_width=True, hide_index=True)

else:
    st.info("Brak danych w bazie. System czeka na pierwsze zdarzenie z czujnika wyjściowego.")
