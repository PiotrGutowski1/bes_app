import streamlit as st

st.title("Moja Publiczna Baza Danych 🚀")

# 1. Nawiązanie połączenia (Streamlit sam czyta dane z secrets.toml)
# Parametr ttl="10m" sprawia, że wynik jest pamiętany przez 10 minut, 
# co oszczędza zapytania do bazy przy każdym kliknięciu na stronie.
conn = st.connection("moja_baza", type="sql")

# 2. Pobranie danych
# Upewnij się, że tabela 'users' (lub inna) istnieje w Twojej bazie
try:
    df = conn.query('SELECT * FROM users LIMIT 100;', ttl="10m")
    
    # 3. Wyświetlenie danych w interaktywnej tabeli
    st.dataframe(df)

except Exception as e:
    st.error(f"Nie udało się pobrać danych. Błąd: {e}")
