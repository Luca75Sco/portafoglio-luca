import math
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Hedge Fund Dashboard Luca", layout="wide")

st.title("🏦 Hedge Fund Dashboard - Luca")

# =========================
# CONFIG ETF
# =========================
ETF_CONFIG = {
    "SWDA": {"nome": "MSCI World", "isin": "IE00B4L5Y983", "target": 0.50, "ticker": "SWDA.L"},
    "EIMI": {"nome": "Emerging Markets", "isin": "IE00BKM4GZ66", "target": 0.12, "ticker": "EIMI.L"},
    "WSML": {"nome": "World Small Cap", "isin": "IE00BF4RFH31", "target": 0.08, "ticker": "WSML.L"},
    "AGGH": {"nome": "Global Aggregate Bond", "isin": "IE00BDBRDM35", "target": 0.12, "ticker": "AGGH.L"},
    "IBGS": {"nome": "Gov Bond 1-3yr", "isin": "IE00B14X4Q57", "target": 0.08, "ticker": "IBGS.L"},
    "SGLD": {"nome": "Gold", "isin": "IE00B579F325", "target": 0.07, "ticker": "SGLD.L"},
    "CMOD": {"nome": "Commodities", "isin": "IE00BD6FTQ80", "target": 0.03, "ticker": "CMOD.L"},
}

# =========================
# FUNZIONI
# =========================
def euro(x):
    return f"{x:,.0f} €".replace(",", ".")

@st.cache_data(ttl=3600)
def get_prices():
    prezzi = {}
    for etf, cfg in ETF_CONFIG.items():
        try:
            data = yf.Ticker(cfg["ticker"]).history(period="5d")
            prezzi[etf] = float(data["Close"].iloc[-1])
        except:
            prezzi[etf] = 0
    return prezzi

@st.cache_data(ttl=3600)
def get_market():
    return yf.Ticker("^GSPC").history(period="1y")

# =========================
# INPUT
# =========================
st.sidebar.header("💰 PAC")
pac_base = st.sidebar.number_input("PAC base", value=1000)

st.sidebar.header("💼 Liquidità")
liquidita = st.sidebar.number_input("Liquidità", value=30000)

st.sidebar.header("🛡️ Riserva %")
perc_riserva = st.sidebar.slider("Riserva %", 5, 30, 20)

st.sidebar.header("📊 ETF Valori")

valori = {}
for etf in ETF_CONFIG:
    valori[etf] = st.sidebar.number_input(f"{etf}", value=5000)

# =========================
# DATI
# =========================
prezzi = get_prices()
market = get_market()

returns = market["Close"].pct_change()
vol = returns.std() * np.sqrt(252)

rolling_max = market["Close"].cummax()
drawdown = (market["Close"] - rolling_max) / rolling_max
max_dd = drawdown.min()

var_1m = (market["Close"].iloc[-1] - market["Close"].iloc[-22]) / market["Close"].iloc[-22]

# =========================
# REGIME
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

mult = {
    "CRISI": 2.0,
    "STRESS": 1.6,
    "OPPORTUNITÀ": 1.3,
    "NORMALE": 1.0,
    "ECCESSO": 0.6
}

pac = pac_base * mult[regime]

# =========================
# RISERVA
# =========================
tot_etf = sum(valori.values())
capitale = tot_etf + liquidita

riserva_target = capitale * perc_riserva / 100

if regime == "CRISI":
    uso_riserva = riserva_target * 0.5
elif regime == "STRESS":
    uso_riserva = riserva_target * 0.25
elif regime == "OPPORTUNITÀ":
    uso_riserva = riserva_target * 0.1
else:
    uso_riserva = 0

uso_riserva = min(uso_riserva, liquidita)

# =========================
# METRICHE
# =========================
st.subheader("📊 Mercato")

c1, c2, c3 = st.columns(3)
c1.metric("Vol", f"{vol*100:.2f}%")
c2.metric("Drawdown", f"{max_dd*100:.2f}%")
c3.metric("Regime", regime)

# =========================
# ETF ANALISI
# =========================
righe = []
sottopesati = {}

for etf, cfg in ETF_CONFIG.items():
    val = valori[etf]
    peso = val / tot_etf
    target = cfg["target"]
    diff = peso - target

    if diff < 0:
        sottopesati[etf] = abs(diff)

    righe.append({
        "ETF": etf,
        "ISIN": cfg["isin"],
        "Prezzo": round(prezzi[etf], 2),
        "Target %": target*100,
        "Attuale %": peso*100,
        "Scostamento %": diff*100
    })

df = pd.DataFrame(righe)

# =========================
# COLORI
# =========================
def color(row):
    if row["Scostamento %"] < -2:
        return ["background-color: #2ecc71"]*len(row)  # verde
    elif row["Scostamento %"] > 2:
        return ["background-color: #e74c3c"]*len(row)  # rosso
    else:
        return [""]*len(row)

st.subheader("📊 Stato ETF")

st.dataframe(df.style.apply(color, axis=1), use_container_width=True)

# =========================
# PRIORITÀ ACQUISTI
# =========================
budget = pac + uso_riserva

st.subheader("💰 Budget")
st.metric("Totale investibile", euro(budget))

# ordina per sottopeso maggiore
sorted_etf = sorted(sottopesati.items(), key=lambda x: x[1], reverse=True)

st.subheader("🛒 Piano acquisti PRIORITARIO")

tot_gap = sum(sottopesati.values())

for etf, gap in sorted_etf:
    quota = gap / tot_gap
    euro_alloc = budget * quota
    prezzo = prezzi[etf]

    if prezzo > 0:
        quote = int(euro_alloc / prezzo)
    else:
        quote = 0

    if quote > 0:
        st.success(f"{etf} → PRIORITÀ ALTA | {quote} quote | {round(euro_alloc)}€")
    else:
        st.info(f"{etf} → accumula budget")

# =========================
# GRAFICO
# =========================
st.subheader("📉 S&P500")
st.line_chart(market["Close"])
