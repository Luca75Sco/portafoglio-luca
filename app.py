import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Portafoglio Hedge Luca PRO", layout="wide")

st.title("📊 Dashboard Portafoglio PRO")

# =========================
# SIDEBAR
# =========================
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

# =========================
# DATI MERCATO (CACHED)
# =========================
@st.cache_data(ttl=3600)
def get_data():
    sp500 = yf.Ticker("^GSPC")
    data = sp500.history(period="6mo")
    return data

try:
    data = get_data()

    if not data.empty:
        prezzi = data["Close"]

        # rendimento 1 mese (~22 giorni)
        if len(prezzi) > 22:
            var_1m = (prezzi.iloc[-1] - prezzi.iloc[-22]) / prezzi.iloc[-22]
        else:
            var_1m = 0

        # volatilità
        returns = prezzi.pct_change()
        vol = returns.std() * (252 ** 0.5)

        # drawdown
        rolling_max = prezzi.cummax()
        drawdown = (prezzi - rolling_max) / rolling_max
        max_dd = drawdown.min()

    else:
        var_1m = 0
        vol = 0
        max_dd = 0

except Exception as e:
    st.warning(f"Errore dati mercato: {e}")
    var_1m = 0
    vol = 0
    max_dd = 0

# =========================
# SEGNALE INTELLIGENTE
# =========================
if var_1m < -0.20 or max_dd < -0.25:
    segnale = "CRASH"
elif var_1m < -0.10:
    segnale = "AGGRESSIVO"
elif var_1m < -0.03:
    segnale = "ACCUMULO"
elif var_1m > 0.10:
    segnale = "PRUDENTE"
else:
    segnale = "NEUTRO"

# =========================
# PAC DINAMICO
# =========================
PAC_BASE = 1000

moltiplicatori = {
    "CRASH": 1.8,
    "AGGRESSIVO": 1.5,
    "ACCUMULO": 1.2,
    "NEUTRO": 1.0,
    "PRUDENTE": 0.7
}

pac = PAC_BASE * moltiplicatori[segnale]

# =========================
# ALLOCAZIONE
# =========================
tot = sum(valori.values())
alloc = {k: v/tot for k,v in valori.items()}

# =========================
# UI - MERCATO
# =========================
st.subheader("📈 Stato Mercato")

col1, col2, col3 = st.columns(3)

col1.metric("S&P500 1M", f"{round(var_1m*100,2)}%")
col2.metric("Volatilità", f"{round(vol*100,2)}%")
col3.metric("Max Drawdown", f"{round(max_dd*100,2)}%")

st.metric("Segnale", segnale)

# =========================
# GRAFICO
# =========================
st.subheader("📊 S&P500 Trend")
st.line_chart(data["Close"])

# =========================
# STRATEGIA
# =========================
st.subheader("💰 Strategia Dinamica")

st.metric("PAC suggerito", f"{round(pac)} €")

if segnale == "CRASH":
    st.error("🚨 MERCATO IN PANICO → ENTRA FORTE")
elif segnale == "AGGRESSIVO":
    st.warning("🔥 Opportunità forte")
elif segnale == "ACCUMULO":
    st.info("📥 Accumulo intelligente")
elif segnale == "PRUDENTE":
    st.warning("⚠️ Mercato tirato → riduci ingressi")
else:
    st.success("😐 Situazione neutra")

# =========================
# ALLOCAZIONE VISIVA
# =========================
st.subheader("📊 Allocazione Attuale")
df_alloc = pd.DataFrame({
    "Asset": list(alloc.keys()),
    "Percentuale": list(alloc.values())
})
st.bar_chart(df_alloc.set_index("Asset"))

# =========================
# RIBILANCIAMENTO
# =========================
st.subheader("⚖️ Ribilanciamento Intelligente")

for asset in target:
    diff = alloc[asset] - target[asset]

    if abs(diff) > 0.05:
        if diff > 0:
            st.error(f"🔻 VENDI {asset} ({round(diff*100,2)}%)")
        else:
            st.success(f"🟢 COMPRA {asset} ({round(abs(diff)*100,2)}%)")
    else:
        st.info(f"{asset}: OK")

# =========================
# BONUS PRO
# =========================
st.subheader("🧠 Insight PRO")

if vol > 0.25:
    st.warning("Mercato molto volatile → opportunità ma rischio alto")

if max_dd < -0.20:
    st.success("Storicamente queste zone sono ottime per accumulo")

if var_1m > 0.15:
    st.warning("Possibile eccesso → attenzione a correzioni")
