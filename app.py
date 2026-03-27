import math
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Hedge Fund Dashboard Luca PRO", layout="wide")

st.title("🏦 Hedge Fund Dashboard - Luca PRO")

# =========================
# CONFIG ETF PORTAFOGLIO
# =========================
ETF_CONFIG = {
    "SWDA": {
        "nome": "iShares Core MSCI World",
        "isin": "IE00B4L5Y983",
        "target": 0.50,
        "ticker_yf": "SWDA.MI",
    },
    "EIMI": {
        "nome": "iShares Core MSCI EM IMI",
        "isin": "IE00BKM4GZ66",
        "target": 0.12,
        "ticker_yf": "EIMI.MI",
    },
    "WSML": {
        "nome": "iShares MSCI World Small Cap",
        "isin": "IE00BF4RFH31",
        "target": 0.08,
        "ticker_yf": "WSML.MI",
    },
    "AGGH": {
        "nome": "iShares Global Aggregate Bond Hedged",
        "isin": "IE00BDBRDM35",
        "target": 0.12,
        "ticker_yf": "AGGH.MI",
    },
    "IBGS": {
        "nome": "iShares € Govt Bond 1-3yr",
        "isin": "IE00B14X4Q57",
        "target": 0.08,
        "ticker_yf": "IBGS.MI",
    },
    "SGLD": {
        "nome": "Invesco Physical Gold ETC",
        "isin": "IE00B579F325",
        "target": 0.07,
        "ticker_yf": "SGLD.MI",
    },
    "CMOD": {
        "nome": "Invesco Bloomberg Commodity",
        "isin": "IE00BD6FTQ80",
        "target": 0.03,
        "ticker_yf": "CMOD.MI",
    },
}

# =========================
# SIDEBAR
# =========================
st.sidebar.header("💼 Patrimonio extra ETF")

immobili_valore = st.sidebar.number_input(
    "Valore Immobili", min_value=0.0, value=300000.0, step=1000.0
)
immobili_rendita = st.sidebar.number_input(
    "Rendita Mensile Immobili", min_value=0.0, value=870.0, step=50.0
)
liquidita = st.sidebar.number_input(
    "Liquidità totale", min_value=0.0, value=30000.0, step=500.0
)

st.sidebar.header("💰 Flussi")
pac_base = st.sidebar.number_input(
    "PAC mensile base", min_value=0.0, value=1000.0, step=100.0
)
versamento_riserva = st.sidebar.number_input(
    "Versamento mensile separato per riserva",
    min_value=0.0,
    value=0.0,
    step=100.0,
)

st.sidebar.header("🛡️ Riserva strategica")
percentuale_riserva = st.sidebar.slider(
    "Riserva % del capitale investibile", min_value=5, max_value=30, value=20
)

st.sidebar.header("⚖️ Ribilanciamento")
soglia_ribilanciamento = st.sidebar.slider(
    "Soglia ribilanciamento (%)", min_value=1, max_value=10, value=3
)

# =========================
# INPUT QUOTE ETF
# =========================
st.subheader("📥 Inserisci le quote dei tuoi ETF")

quote_etf = {}

col1, col2 = st.columns(2)

keys_left = ["SWDA", "EIMI", "WSML", "AGGH"]
keys_right = ["IBGS", "SGLD", "CMOD"]

with col1:
    for k in keys_left:
        quote_etf[k] = st.number_input(
            f"Quote {k} - {ETF_CONFIG[k]['nome']}",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

with col2:
    for k in keys_right:
        quote_etf[k] = st.number_input(
            f"Quote {k} - {ETF_CONFIG[k]['nome']}",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )

# =========================
# DATI MERCATO - REGIME
# =========================
@st.cache_data(ttl=3600)
def get_market_data():
    return yf.Ticker("^GSPC").history(period="1y")


# =========================
# PREZZI LIVE ETF - REFRESH MANUALE
# =========================
def scarica_prezzi_live():
    prezzi = {}
    errori = {}

    for ticker_portafoglio, info in ETF_CONFIG.items():
        ticker_yf = info["ticker_yf"]
        try:
            hist = yf.Ticker(ticker_yf).history(period="5d")
            if hist.empty or "Close" not in hist.columns:
                prezzi[ticker_portafoglio] = 0.0
                errori[ticker_portafoglio] = f"Nessun dato disponibile per {ticker_yf}"
            else:
                close_series = hist["Close"].dropna()
                if close_series.empty:
                    prezzi[ticker_portafoglio] = 0.0
                    errori[ticker_portafoglio] = f"Prezzo non disponibile per {ticker_yf}"
                else:
                    prezzi[ticker_portafoglio] = float(close_series.iloc[-1])
                    errori[ticker_portafoglio] = ""
        except Exception as e:
            prezzi[ticker_portafoglio] = 0.0
            errori[ticker_portafoglio] = str(e)

    return prezzi, errori


if "prezzi_live" not in st.session_state:
    st.session_state.prezzi_live = {}
if "errori_prezzi" not in st.session_state:
    st.session_state.errori_prezzi = {}

if st.button("🔄 Aggiorna prezzi live ETF"):
    prezzi_live_tmp, errori_tmp = scarica_prezzi_live()
    st.session_state.prezzi_live = prezzi_live_tmp
    st.session_state.errori_prezzi = errori_tmp

if not st.session_state.prezzi_live:
    prezzi_live_tmp, errori_tmp = scarica_prezzi_live()
    st.session_state.prezzi_live = prezzi_live_tmp
    st.session_state.errori_prezzi = errori_tmp

prezzi_live = st.session_state.prezzi_live
errori_prezzi = st.session_state.errori_prezzi

# =========================
# CALCOLO REGIME DI MERCATO
# =========================
try:
    market_data = get_market_data()

    if market_data.empty or "Close" not in market_data.columns:
        prezzi_mercato = pd.Series(dtype=float)
        vol = 0.0
        max_dd = 0.0
        var_1m = 0.0
    else:
        prezzi_mercato = market_data["Close"].dropna()
        returns_mercato = prezzi_mercato.pct_change().dropna()

        vol = float(returns_mercato.std() * np.sqrt(252)) if len(returns_mercato) > 1 else 0.0

        rolling_max = prezzi_mercato.cummax()
        drawdown = (prezzi_mercato - rolling_max) / rolling_max
        max_dd = float(drawdown.min()) if len(drawdown) > 0 else 0.0

        if len(prezzi_mercato) > 22 and prezzi_mercato.iloc[-22] != 0:
            var_1m = float(
                (prezzi_mercato.iloc[-1] - prezzi_mercato.iloc[-22]) / prezzi_mercato.iloc[-22]
            )
        else:
            var_1m = 0.0

except Exception as e:
    st.warning(f"Errore nel recupero dati di mercato: {e}")
    prezzi_mercato = pd.Series(dtype=float)
    vol = 0.0
    max_dd = 0.0
    var_1m = 0.0

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

moltiplicatori_pac = {
    "CRISI": 2.0,
    "STRESS": 1.6,
    "OPPORTUNITÀ": 1.3,
    "NORMALE": 1.0,
    "ECCESSO": 0.6,
}
pac_suggerito = pac_base * moltiplicatori_pac[regime]

# =========================
# CALCOLO VALORI ETF
# =========================
valori_etf = {}
righe_etf = []

for ticker, info in ETF_CONFIG.items():
    prezzo = prezzi_live.get(ticker, 0.0)
    quote = quote_etf.get(ticker, 0.0)
    valore = quote * prezzo
    valori_etf[ticker] = valore

tot_etf = sum(valori_etf.values())

for ticker, info in ETF_CONFIG.items():
    prezzo = prezzi_live.get(ticker, 0.0)
    quote = quote_etf.get(ticker, 0.0)
    valore = valori_etf.get(ticker, 0.0)
    target = info["target"]

    alloc_attuale = valore / tot_etf if tot_etf > 0 else 0.0
    scostamento = alloc_attuale - target
    valore_target = tot_etf * target
    da_comprare_target = max(valore_target - valore, 0.0)

    if abs(scostamento) * 100 < soglia_ribilanciamento:
        indicazione = "OK"
    elif scostamento < 0:
        indicazione = "COMPRA"
    else:
        indicazione = "SOVRAPPESO"

    righe_etf.append(
        {
            "Ticker": ticker,
            "ETF": info["nome"],
            "ISIN": info["isin"],
            "Prezzo live €": round(prezzo, 2),
            "Quote": round(quote, 4),
            "Valore attuale €": round(valore, 2),
            "Target %": round(target * 100, 2),
            "Attuale %": round(alloc_attuale * 100, 2),
            "Scostamento %": round(scostamento * 100, 2),
            "Da comprare per target €": round(da_comprare_target, 2),
            "Indicazione": indicazione,
        }
    )

df_etf = pd.DataFrame(righe_etf)

# =========================
# PATRIMONIO
# =========================
portafoglio_finanziario = tot_etf
totale = portafoglio_finanziario + immobili_valore + liquidita
capitale_investibile = portafoglio_finanziario + liquidita

# =========================
# RISERVA STRATEGICA
# =========================
riserva_target = capitale_investibile * percentuale_riserva / 100.0
liquidita_libera = max(liquidita - riserva_target, 0.0)

if regime == "CRISI":
    uso_riserva = riserva_target * 0.50
elif regime == "STRESS":
    uso_riserva = riserva_target * 0.25
elif regime == "OPPORTUNITÀ":
    uso_riserva = riserva_target * 0.10
else:
    uso_riserva = 0.0

# =========================
# STATO MERCATO
# =========================
st.subheader("📊 Stato Mercato")

c1, c2, c3 = st.columns(3)
c1.metric("Volatilità", f"{vol*100:.2f}%")
c2.metric("Max Drawdown", f"{max_dd*100:.2f}%")
c3.metric("Regime", regime)

st.subheader("💰 Strategia PAC")

c1, c2 = st.columns(2)
c1.metric("PAC mensile base", f"{pac_base:,.0f} €".replace(",", "."))
c2.metric("PAC mensile suggerito", f"{pac_suggerito:,.0f} €".replace(",", "."))

if regime == "CRISI":
    st.error("🚨 Massimo panico: aumenta il PAC e valuta uso graduale della riserva.")
elif regime == "STRESS":
    st.warning("🔥 Mercato in stress: PAC più alto e possibile uso parziale della riserva.")
elif regime == "OPPORTUNITÀ":
    st.info("📥 Correzione interessante: PAC sopra base e uso leggero della riserva.")
elif regime == "ECCESSO":
    st.warning("⚠️ Mercato tirato: PAC ridotto e riserva da preservare.")
else:
    st.success("✔️ Mercato normale: mantieni la strategia standard.")

# =========================
# RISERVA
# =========================
st.subheader("💣 Riserva Strategica Separata")

c1, c2, c3 = st.columns(3)
c1.metric("Riserva target", f"{riserva_target:,.0f} €".replace(",", "."))
c2.metric("Liquidità attuale", f"{liquidita:,.0f} €".replace(",", "."))
c3.metric("Uso teorico riserva", f"{uso_riserva:,.0f} €".replace(",", "."))

if liquidita < riserva_target:
    st.warning(
        f"⚠️ Riserva sotto target di {(riserva_target - liquidita):,.0f} €".replace(",", ".")
    )
else:
    st.success(
        f"✔️ Riserva coperta. Liquidità libera oltre riserva: {liquidita_libera:,.0f} €".replace(",", ".")
    )

st.caption("La riserva è separata dal PAC e non viene inclusa nel ribilanciamento mensile.")

# =========================
# PATRIMONIO TOTALE
# =========================
st.subheader("🏦 Patrimonio Totale")

c1, c2, c3 = st.columns(3)
c1.metric("Totale", f"{totale:,.0f} €".replace(",", "."))
c2.metric("ETF", f"{portafoglio_finanziario:,.0f} €".replace(",", "."))
c3.metric("Rendita immobili annua", f"{immobili_rendita * 12:,.0f} €".replace(",", "."))

# =========================
# ALLOCAZIONE GLOBALE
# =========================
st.subheader("📊 Allocazione Globale")

if totale > 0:
    alloc_tot = {
        "ETF": portafoglio_finanziario / totale,
        "Immobili": immobili_valore / totale,
        "Liquidità": liquidita / totale,
    }
else:
    alloc_tot = {"ETF": 0.0, "Immobili": 0.0, "Liquidità": 0.0}

df_alloc = pd.DataFrame({"Asset": list(alloc_tot.keys()), "Peso": list(alloc_tot.values())})
st.bar_chart(df_alloc.set_index("Asset"))

# =========================
# TABELLA ETF COLORATA
# =========================
st.subheader("📊 ETF Portafoglio Reale con Prezzi Live")

def colora_riga(riga):
    if riga["Indicazione"] == "COMPRA":
        return ["background-color: #d4edda"] * len(riga)
    if riga["Indicazione"] == "SOVRAPPESO":
        return ["background-color: #f8d7da"] * len(riga)
    return ["background-color: #ffffff"] * len(riga)

st.dataframe(df_etf.style.apply(colora_riga, axis=1), use_container_width=True)

if errori_prezzi:
    with st.expander("Dettaglio eventuali errori prezzi live"):
        for k, v in errori_prezzi.items():
            if v:
                st.write(f"{k}: {v}")

# =========================
# RIBILANCIAMENTO BUY ONLY
# =========================
st.subheader("🛒 Piano Acquisti Ottimizzato (solo acquisti)")

sottopesati = {}

for ticker, info in ETF_CONFIG.items():
    valore = valori_etf.get(ticker, 0.0)
    target = info["target"]
    alloc_attuale = valore / tot_etf if tot_etf > 0 else 0.0
    gap = target - alloc_attuale

    if gap > (soglia_ribilanciamento / 100):
        sottopesati[ticker] = gap

tot_gap = sum(sottopesati.values())

piano_acquisti = []
if tot_gap > 0 and pac_suggerito > 0:
    for ticker, gap in sottopesati.items():
        quota_budget = gap / tot_gap
        euro_da_destinare = pac_suggerito * quota_budget
        prezzo = prezzi_live.get(ticker, 0.0)

        quote_intere = math.floor(euro_da_destinare / prezzo) if prezzo > 0 else 0
        controvalore_quote = quote_intere * prezzo

        piano_acquisti.append(
            {
                "Ticker": ticker,
                "ETF": ETF_CONFIG[ticker]["nome"],
                "ISIN": ETF_CONFIG[ticker]["isin"],
                "Prezzo live €": round(prezzo, 2),
                "Budget teorico €": round(euro_da_destinare, 2),
                "Quote acquistabili": int(quote_intere),
                "Controvalore quote €": round(controvalore_quote, 2),
            }
        )

if piano_acquisti:
    df_piano = pd.DataFrame(piano_acquisti)
    st.dataframe(df_piano, use_container_width=True)

    for _, row in df_piano.iterrows():
        if row["Quote acquistabili"] > 0:
            st.success(
                f"🟢 {row['Ticker']}: compra {row['Quote acquistabili']} quote "
                f"(circa {row['Controvalore quote €']:.2f} €)"
            )
        else:
            st.info(
                f"{row['Ticker']}: budget teorico {row['Budget teorico €']:.2f} €, "
                f"non sufficiente per 1 quota intera"
            )
else:
    st.info("Nessun ETF da ribilanciare oltre la soglia impostata oppure PAC pari a zero.")

st.caption("Ribilanciamento solo in acquisto: nessuna vendita, per efficienza fiscale.")

# =========================
# SIMULATORE
# =========================
st.subheader("🚀 Simulatore verso 1M €")

anni = st.slider("Orizzonte anni", min_value=5, max_value=25, value=15)
rendimento = st.slider("Rendimento atteso % annuo", min_value=3, max_value=10, value=6)

capitale = portafoglio_finanziario
storico = []

for _ in range(anni * 12):
    capitale = capitale * (1 + rendimento / 100 / 12) + pac_suggerito
    storico.append(capitale)

df_storico = pd.DataFrame({"Capitale": storico})
st.line_chart(df_storico)
st.metric("Valore finale stimato", f"{capitale:,.0f} €".replace(",", "."))

# =========================
# DECISION ENGINE
# =========================
st.subheader("🧠 Decision Engine")

if regime == "CRISI":
    st.error("🚨 Massimo panico: aumenta il PAC e valuta uso graduale della riserva.")
elif regime == "STRESS":
    st.warning("🔥 Mercato in stress: PAC più alto e possibile uso parziale della riserva.")
elif regime == "OPPORTUNITÀ":
    st.info("📥 Correzione interessante: PAC sopra base e uso leggero della riserva.")
elif regime == "ECCESSO":
    st.warning("⚠️ Mercato tirato: PAC ridotto e riserva da preservare.")
else:
    st.success("✔️ Mercato normale: mantieni la strategia standard.")

if max_dd < -0.25:
    st.success("👉 Zona storicamente favorevole per ingressi progressivi.")

# =========================
# GRAFICO MERCATO
# =========================
st.subheader("📉 S&P500")

if len(prezzi_mercato) > 0:
    st.line_chart(prezzi_mercato)
else:
    st.info("Dati di mercato non disponibili al momento.")
