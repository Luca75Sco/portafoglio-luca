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

azionario = st.sidebar.number_input(
    "ETF Azionario totale", min_value=0.0, value=25000.0, step=500.0
)
obbligazionario = st.sidebar.number_input(
    "ETF Obbligazionario totale", min_value=0.0, value=8000.0, step=500.0
)
oro = st.sidebar.number_input(
    "Oro", min_value=0.0, value=2000.0, step=100.0
)
commodities = st.sidebar.number_input(
    "Commodities", min_value=0.0, value=2000.0, step=100.0
)

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

# =========================
# DATI MERCATO
# =========================
@st.cache_data(ttl=3600)
def get_data():
    return yf.Ticker("^GSPC").history(period="1y")


try:
    data = get_data()

    if data.empty or "Close" not in data.columns:
        prezzi = pd.Series(dtype=float)
        vol = 0.0
        max_dd = 0.0
        var_1m = 0.0
    else:
        prezzi = data["Close"].dropna()
        returns = prezzi.pct_change().dropna()

        vol = float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0

        rolling_max = prezzi.cummax()
        drawdown = (prezzi - rolling_max) / rolling_max
        max_dd = float(drawdown.min()) if len(drawdown) > 0 else 0.0

        if len(prezzi) > 22 and prezzi.iloc[-22] != 0:
            var_1m = float((prezzi.iloc[-1] - prezzi.iloc[-22]) / prezzi.iloc[-22])
        else:
            var_1m = 0.0

except Exception as e:
    st.warning(f"Errore nel recupero dati di mercato: {e}")
    prezzi = pd.Series(dtype=float)
    vol = 0.0
    max_dd = 0.0
    var_1m = 0.0

# =========================
# REGIME DI MERCATO
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
moltiplicatori_pac = {
    "CRISI": 2.0,
    "STRESS": 1.6,
    "OPPORTUNITÀ": 1.3,
    "NORMALE": 1.0,
    "ECCESSO": 0.6,
}

pac_suggerito = pac_base * moltiplicatori_pac[regime]

# =========================
# PATRIMONIO
# =========================
portafoglio_finanziario = azionario + obbligazionario + oro + commodities
totale = portafoglio_finanziario + immobili_valore + liquidita
capitale_investibile = portafoglio_finanziario + liquidita

# =========================
# RISERVA STRATEGICA SEPARATA
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
    st.error("🚨 Massimo panico: aumenta il PAC e valuta un ingresso dalla riserva.")
elif regime == "STRESS":
    st.warning("🔥 Mercato in stress: PAC più alto e possibile uso parziale della riserva.")
elif regime == "OPPORTUNITÀ":
    st.info("📥 Correzione interessante: PAC sopra base e uso leggero della riserva.")
elif regime == "ECCESSO":
    st.warning("⚠️ Mercato tirato: PAC ridotto e priorità alla conservazione della riserva.")
else:
    st.success("✔️ Mercato normale: mantieni la strategia standard.")

# =========================
# RISERVA
# =========================
st.subheader("💣 Riserva Strategica Separata")

c1, c2, c3 = st.columns(3)
c1.metric("Riserva target", f"{riserva_target:,.0f} €".replace(",", "."))
c2.metric("Liquidità attuale", f"{liquidita:,.0f} €".replace(",", "."))
c3.metric("Versamento mensile riserva", f"{versamento_riserva:,.0f} €".replace(",", "."))

if liquidita < riserva_target:
    gap_riserva = riserva_target - liquidita
    st.warning(f"⚠️ Riserva sotto target di {gap_riserva:,.0f} €".replace(",", "."))
else:
    surplus = liquidita - riserva_target
    st.success(f"✔️ Riserva coperta. Eccedenza oltre target: {surplus:,.0f} €".replace(",", "."))

st.info("La riserva è separata dal PAC: il PAC investe nel portafoglio, la riserva si costruisce e si gestisce a parte.")

st.subheader("⚡ Utilizzo Strategico della Riserva")

c1, c2 = st.columns(2)
c1.metric("Uso teorico riserva", f"{uso_riserva:,.0f} €".replace(",", "."))
c2.metric("Liquidità libera oltre riserva", f"{liquidita_libera:,.0f} €".replace(",", "."))

# =========================
# PATRIMONIO TOTALE
# =========================
st.subheader("🏦 Patrimonio Totale")

c1, c2, c3 = st.columns(3)
c1.metric("Totale", f"{totale:,.0f} €".replace(",", "."))
c2.metric("Finanziario", f"{portafoglio_finanziario:,.0f} €".replace(",", "."))
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
    alloc_tot = {
        "ETF": 0.0,
        "Immobili": 0.0,
        "Liquidità": 0.0,
    }

df_alloc = pd.DataFrame(
    {
        "Asset": list(alloc_tot.keys()),
        "Peso": list(alloc_tot.values()),
    }
)

st.bar_chart(df_alloc.set_index("Asset"))

# =========================
# ETF REALI DEL PORTAFOGLIO
# =========================
st.subheader("📊 ETF Portafoglio Reale")

etf_data = {
    "SWDA": {
        "nome": "iShares Core MSCI World",
        "isin": "IE00B4L5Y983",
        "target": 0.50,
        "default": azionario * (50 / 70),
    },
    "EIMI": {
        "nome": "iShares Core MSCI EM IMI",
        "isin": "IE00BKM4GZ66",
        "target": 0.12,
        "default": azionario * (12 / 70),
    },
    "WSML": {
        "nome": "iShares MSCI World Small Cap",
        "isin": "IE00BF4RFH31",
        "target": 0.08,
        "default": azionario * (8 / 70),
    },
    "AGGH": {
        "nome": "iShares Global Aggregate Hedged",
        "isin": "IE00BDBRDM35",
        "target": 0.12,
        "default": obbligazionario * (12 / 20),
    },
    "IBGS": {
        "nome": "iShares € Govt Bond 1-3yr",
        "isin": "IE00B14X4Q57",
        "target": 0.08,
        "default": obbligazionario * (8 / 20),
    },
    "SGLD": {
        "nome": "Invesco Physical Gold ETC",
        "isin": "IE00B579F325",
        "target": 0.07,
        "default": oro,
    },
    "CMOD": {
        "nome": "Invesco Bloomberg Commodity",
        "isin": "IE00BD6FTQ80",
        "target": 0.03,
        "default": commodities,
    },
}

st.write("Inserisci i valori attuali dei singoli ETF")

valori_etf = {}

col1, col2 = st.columns(2)

with col1:
    valori_etf["SWDA"] = st.number_input(
        "SWDA / iShares Core MSCI World (€)",
        min_value=0.0,
        value=float(etf_data["SWDA"]["default"]),
        step=100.0,
    )
    valori_etf["EIMI"] = st.number_input(
        "EIMI / iShares Core MSCI EM IMI (€)",
        min_value=0.0,
        value=float(etf_data["EIMI"]["default"]),
        step=100.0,
    )
    valori_etf["WSML"] = st.number_input(
        "WSML / iShares MSCI World Small Cap (€)",
        min_value=0.0,
        value=float(etf_data["WSML"]["default"]),
        step=100.0,
    )
    valori_etf["AGGH"] = st.number_input(
        "AGGH / iShares Global Aggregate Hedged (€)",
        min_value=0.0,
        value=float(etf_data["AGGH"]["default"]),
        step=100.0,
    )

with col2:
    valori_etf["IBGS"] = st.number_input(
        "IBGS / iShares € Govt Bond 1-3yr (€)",
        min_value=0.0,
        value=float(etf_data["IBGS"]["default"]),
        step=100.0,
    )
    valori_etf["SGLD"] = st.number_input(
        "SGLD / Invesco Physical Gold ETC (€)",
        min_value=0.0,
        value=float(etf_data["SGLD"]["default"]),
        step=100.0,
    )
    valori_etf["CMOD"] = st.number_input(
        "CMOD / Invesco Bloomberg Commodity (€)",
        min_value=0.0,
        value=float(etf_data["CMOD"]["default"]),
        step=100.0,
    )

tot_etf = sum(valori_etf.values())

righe = []
sottopesati = {}

for ticker, dati in etf_data.items():
    valore = valori_etf.get(ticker, 0.0)
    alloc_attuale = valore / tot_etf if tot_etf > 0 else 0.0
    target = dati["target"]
    scostamento = alloc_attuale - target

    importo_target = tot_etf * target
    gap_acquisto = max(importo_target - valore, 0.0)

    if scostamento < -0.001:
        sottopesati[ticker] = abs(scostamento)

    if gap_acquisto > 0:
        azione = "COMPRA"
    else:
        azione = "OK / SOPRAPPESO"

    righe.append(
        {
            "Ticker": ticker,
            "ETF": dati["nome"],
            "ISIN": dati["isin"],
            "Target %": round(target * 100, 2),
            "Attuale %": round(alloc_attuale * 100, 2),
            "Scostamento %": round(scostamento * 100, 2),
            "Valore attuale €": round(valore, 0),
            "Da comprare per target €": round(gap_acquisto, 0),
            "Indicazione": azione,
        }
    )

df_etf = pd.DataFrame(righe)
st.dataframe(df_etf, use_container_width=True)

# =========================
# RIBILANCIAMENTO SOLO IN ACQUISTO
# =========================
st.subheader("🛒 Piano Acquisti Ottimizzato (solo acquisti)")

budget_ribilanciamento = pac_suggerito
tot_gap = sum(sottopesati.values())

if tot_gap > 0 and budget_ribilanciamento > 0:
    piano = []

    for ticker, gap in sottopesati.items():
        quota = gap / tot_gap
        acquisto = budget_ribilanciamento * quota
        piano.append(
            {
                "Ticker": ticker,
                "ETF": etf_data[ticker]["nome"],
                "ISIN": etf_data[ticker]["isin"],
                "Budget acquisto €": round(acquisto, 0),
            }
        )

    df_piano = pd.DataFrame(piano)
    st.dataframe(df_piano, use_container_width=True)

    for _, row in df_piano.iterrows():
        st.success(
            f"🟢 Compra {int(row['Budget acquisto €'])} € di {row['Ticker']} - {row['ETF']}"
        )
else:
    st.info("Portafoglio già ben allineato oppure PAC pari a zero.")

st.caption("Il ribilanciamento è solo in acquisto: nessuna vendita, per massimizzare l'efficienza fiscale.")

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
st.caption("Il simulatore usa il PAC suggerito. La riserva resta separata e non viene investita automaticamente.")

# =========================
# DECISION ENGINE
# =========================
st.subheader("🧠 Decision Engine")

if regime in ["CRISI", "STRESS"]:
    st.success("👉 Azione: aumenta il PAC e valuta un uso graduale della riserva.")
elif regime == "OPPORTUNITÀ":
    st.info("👉 Azione: PAC sopra base; uso riserva solo leggero.")
elif regime == "ECCESSO":
    st.warning("👉 Azione: PAC più prudente; non usare la riserva.")
else:
    st.info("👉 Azione: continua con PAC standard e riserva separata.")

if max_dd < -0.25:
    st.success("👉 Zona storicamente favorevole per ingressi progressivi.")

# =========================
# GRAFICO MERCATO
# =========================
st.subheader("📉 S&P500")

if len(prezzi) > 0:
    st.line_chart(prezzi)
else:
    st.info("Dati di mercato non disponibili al momento.")
