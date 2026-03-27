import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Portafoglio Hedge Luca", layout="wide")

st.title("📊 Dashboard Portafoglio")

st.sidebar.header("Valori Portafoglio")

azionario = st.sidebar.number_input("Azionario", value=25000)
obbligazionario = st.sidebar.number_input("Obbligazionario", value=8000)
oro = st.sidebar.number_input("Oro", value=2000)
commodities = st.sidebar.number_input("Commodities", value=2000)

valori = {
    "Azionario": azionario,
    "Obbligazionario": obbligazionario,
    "Oro": oro,
    "Commodities": commodities
}

target = {
    "Azionario": 0.70,
    "Obbligazionario": 0.20,
    "Oro": 0.05,
    "Commodities": 0.05
}

try:
    sp500 = yf.Ticker("^GSPC")
    data = sp500.history(period="3mo")

    if len(data) > 22:
        var = (data["Close"].iloc[-1] - data["Close"].iloc[-22]) / data["Close"].iloc[-22]
    else:
        var = 0

except:
    var = 0.iloc[-22]

if var < -0.25:
    segnale = "CRASH"
elif var < -0.15:
    segnale = "AGGRESSIVO"
elif var < -0.05:
    segnale = "ACCUMULO"
elif var > 0.1:
    segnale = "PRUDENTE"
else:
    segnale = "NEUTRO"

PAC_BASE = 1000

if segnale == "CRASH":
    pac = PAC_BASE * 1.7
elif segnale == "AGGRESSIVO":
    pac = PAC_BASE * 1.5
elif segnale == "ACCUMULO":
    pac = PAC_BASE * 1.2
elif segnale == "PRUDENTE":
    pac = PAC_BASE * 0.7
else:
    pac = PAC_BASE

tot = sum(valori.values())
alloc = {k: v/tot for k,v in valori.items()}

st.subheader("📈 Stato Mercato")
st.metric("Variazione S&P500", f"{round(var*100,2)}%")
st.metric("Segnale", segnale)

st.subheader("💰 Strategia")
st.metric("PAC suggerito", f"{round(pac)} €")

st.subheader("📊 Allocazione")
for k,v in alloc.items():
    st.write(f"{k}: {round(v*100,2)}%")

st.subheader("⚖️ Ribilanciamento")

for asset in target:
    diff = alloc[asset] - target[asset]
    if abs(diff) > 0.05:
        if diff > 0:
            st.error(f"VENDI {asset}")
        else:
            st.success(f"COMPRA {asset}")
    else:
        st.info(f"{asset}: OK")
