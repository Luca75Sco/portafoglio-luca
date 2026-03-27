import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Hedge Fund Dashboard Luca", layout="wide")

st.title("🏦 Hedge Fund Dashboard - Luca")

# =========================
# INPUT PATRIMONIO
# =========================
st.sidebar.header("💼 Patrimonio")

azionario = st.sidebar.number_input("ETF Azionario", value=25000)
obbligazionario = st.sidebar.number_input("ETF Obbligazionario", value=8000)
oro = st.sidebar.number_input("Oro", value=2000)
commodities = st.sidebar.number_input("Commodities", value=2000)

immobili_valore = st.sidebar.number_input("Valore Immobili", value=300000)
immobili_rendita = st.sidebar.number_input("Rendita Mensile Immobili", value=870)

liquidita = st.sidebar.number_input("Liquidità", value=30000)

PAC_BASE = st.sidebar.number_input("PAC base", value=1000)

# =========================
# DATI MERCATO
# =========================
@st.cache_data(ttl=3600)
def get_data():
    return yf.Ticker("^GSPC").history(period="1y")

data = get_data()
prezzi = data["Close"]

returns = prezzi.pct_change()

# metriche
vol = returns.std() * np.sqrt(252)
rolling_max = prezzi.cummax()
drawdown = (prezzi - rolling_max) / rolling_max
max_dd = drawdown.min()

# rendimento breve
if len(prezzi) > 22:
    var_1m = (prezzi.iloc[-1] - prezzi.iloc[-22]) / prezzi.iloc[-22]
else:
    var_1m = 0

# =========================
# SEGNALE MACRO
# =========================
if max_dd < -0.30:
    regime = "CRISI"
elif max_dd < -0.20:
    regime = "STRESS"
elif var_1m < -0.10:
    regime = "OPPORTUNITÀ"
elif var_1m > 0.12:
    regime = "ECCESSO"
else:
    regime = "NORMALE"

# =========================
# PAC DINAMICO
# =========================
mult = {
    "CRISI": 2.0,
    "STRESS": 1.6,
    "OPPORTUNITÀ": 1.3,
    "NORMALE": 1.0,
    "ECCESSO": 0.6
}

pac = PAC_BASE * mult[regime]

# =========================
# PATRIMONIO
# =========================
portafoglio_finanziario = azionario + obbligazionario + oro + commodities
totale = portafoglio_finanziario + immobili_valore + liquidita

# =========================
# RISERVA STRATEGICA %
# =========================
st.subheader("💣 Riserva Strategica")

percentuale_riserva = st.sidebar.slider("Riserva %", 10, 30, 20)

capitale_investibile = portafoglio_finanziario + liquidita
riserva_target = capitale_investibile * percentuale_riserva / 100

st.metric("Riserva target", f"{round(riserva_target)} €")

if liquidita < riserva_target:
    st.warning("⚠️ Riserva da costruire")
else:
    st.success("✔️ Riserva pronta")

# =========================
# INTEGRAZIONE PAC + RISERVA
# =========================
st.subheader("🔄 Allocazione Flusso Mensile")

flusso = st.sidebar.number_input("Capitale mensile disponibile", value=1000)

allocazione_flusso = {
    "CRISI": (1.0, 0.0),
    "STRESS": (0.8, 0.2),
    "OPPORTUNITÀ": (0.7, 0.3),
    "NORMALE": (0.6, 0.4),
    "ECCESSO": (0.3, 0.7)
}

pac_perc, riserva_perc = allocazione_flusso[regime]

pac_mensile = flusso * pac_perc
riserva_mensile = flusso * riserva_perc

st.metric("PAC mensile effettivo", f"{round(pac_mensile)} €")
st.metric("Accantonamento riserva", f"{round(riserva_mensile)} €")

# =========================
# UTILIZZO RISERVA
# =========================
st.subheader("⚡ Utilizzo Strategico Riserva")

if regime == "CRISI":
    uso = riserva_target * 0.5
    st.error(f"🚨 Usa fino a {round(uso)} € della riserva")

elif regime == "STRESS":
    uso = riserva_target * 0.25
    st.warning(f"👉 Usa circa {round(uso)} €")

elif regime == "OPPORTUNITÀ":
    uso = riserva_target * 0.10
    st.info(f"👉 Uso leggero: {round(uso)} €")

elif regime == "ECCESSO":
    st.success("👉 NON investire: costruisci riserva")

else:
    st.info("👉 Mantieni strategia standard")

# =========================
# UI - MERCATO
# =========================
st.subheader("📊 Stato Mercato")

c1, c2, c3 = st.columns(3)
c1.metric("Volatilità", f"{round(vol*100,2)}%")
c2.metric("Max Drawdown", f"{round(max_dd*100,2)}%")
c3.metric("Regime", regime)

st.subheader("💰 Strategia")

st.metric("PAC teorico (base)", f"{round(pac)} €")

if regime == "CRISI":
    st.error("🚨 MASSIMO PANICO → INVESTI FORTE")
elif regime == "STRESS":
    st.warning("🔥 Mercato in stress → aumenta esposizione")
elif regime == "OPPORTUNITÀ":
    st.info("📥 Fase di accumulo")
elif regime == "ECCESSO":
    st.warning("⚠️ Mercato caro → rallenta")
else:
    st.success("✔️ Normale")

# =========================
# PATRIMONIO
# =========================
st.subheader("🏦 Patrimonio Totale")

c1, c2, c3 = st.columns(3)
c1.metric("Totale", f"{round(totale)} €")
c2.metric("Finanziario", f"{round(portafoglio_finanziario)} €")
c3.metric("Rendita immobili annua", f"{round(immobili_rendita*12)} €")

# =========================
# ALLOCAZIONE
# =========================
st.subheader("📊 Allocazione Globale")

alloc_tot = {
    "ETF": portafoglio_finanziario / totale,
    "Immobili": immobili_valore / totale,
    "Liquidità": liquidita / totale
}

df = pd.DataFrame({
    "Asset": list(alloc_tot.keys()),
    "Peso": list(alloc_tot.values())
})

st.bar_chart(df.set_index("Asset"))

# =========================
# SIMULATORE
# =========================
st.subheader("🚀 Simulatore verso 1M €")

anni = st.slider("Orizzonte anni", 5, 25, 15)
rendimento = st.slider("Rendimento atteso %", 3, 10, 6)

capitale = portafoglio_finanziario
storico = []

for i in range(anni * 12):
    capitale = capitale * (1 + rendimento/100/12) + pac_mensile
    storico.append(capitale)

st.line_chart(storico)

st.metric("Valore finale stimato", f"{round(capitale)} €")

# =========================
# DECISION ENGINE
# =========================
st.subheader("🧠 Decision Engine")

if regime in ["CRISI", "STRESS"]:
    st.success("👉 AZIONE: investi progressivamente + usa riserva")

if regime == "ECCESSO":
    st.warning("👉 AZIONE: accumula riserva")

if max_dd < -0.25:
    st.success("👉 Zona storicamente ottima per entrare")

# =========================
# GRAFICO MERCATO
# =========================
st.subheader("📉 S&P500")
st.line_chart(prezzi)
