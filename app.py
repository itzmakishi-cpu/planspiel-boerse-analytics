import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# PAGE CONFIGURATION (MUSS ZUERST AUFGERUFEN WERDEN)
# ---------------------------------------------------------
st.set_page_config(
    page_title="PLANSPIEL BÖRSE ANALYTICS",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# FUTURISTIC CUSTOM CSS (CLEAN DARK LOOK)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Dark Theme Core */
    .stApp {
        background-color: #060911;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Global Elements hiding (Macht es zur "App") */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Header Card */
    .header-card {
        background: linear-gradient(180deg, #0f172a 0%, #080d1a 100%);
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin-bottom: 16px;
        box-shadow: 0 4px 20px rgba(0, 242, 254, 0.05);
    }
    .header-title {
        font-size: 1.2rem;
        font-weight: 800;
        letter-spacing: 3px;
        color: #38bdf8;
        text-transform: uppercase;
        margin: 0;
    }
    .header-subtitle {
        font-size: 0.7rem;
        color: #64748b;
        letter-spacing: 1.5px;
        margin-top: 4px;
    }

    /* Metric Cards Grid */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 16px;
    }
    .metric-card {
        background: #0d1322;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 12px;
    }
    .metric-label {
        font-size: 0.65rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 2px;
    }

    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .badge-bull { background-color: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981; }
    .badge-bear { background-color: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444; }
    .badge-neu  { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid #f59e0b; }

    /* Erklär-Bär Analytics Box */
    .analysis-card {
        background: linear-gradient(135deg, #0b1329 0%, #111827 100%);
        border: 1px solid #3b82f6;
        border-radius: 14px;
        padding: 16px;
        margin-top: 16px;
        margin-bottom: 16px;
    }
    .analysis-title {
        font-size: 0.8rem;
        font-weight: 800;
        color: #60a5fa;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 10px;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 6px;
    }
    .analysis-p {
        font-size: 0.82rem;
        line-height: 1.5;
        color: #cbd5e1;
        margin-bottom: 10px;
    }

    /* Signal Bar Container */
    .signal-container {
        background: #090e1a;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# WATCHLIST DEFINITION
# ---------------------------------------------------------
WATCHLIST = {
    "SAP SE (DAX)": "SAP.DE",
    "NVIDIA Corp (US)": "NVDA",
    "Apple Inc (US)": "AAPL",
    "Microsoft (US)": "MSFT",
    "Rheinmetall AG (DAX)": "RHM.DE",
    "Tesla Inc (US)": "TSLA",
    "Adidas AG (DAX)": "ADS.DE",
    "Deutsche Bank (DAX)": "DBK.DE",
    "Amazon.com (US)": "AMZN",
    "Allianz SE (DAX)": "ALV.DE"
}

# ---------------------------------------------------------
# HEADER COMPONENT
# ---------------------------------------------------------
st.markdown("""
<div class="header-card">
    <div class="header-title">Planspiel Analytics</div>
    <div class="header-subtitle">SYSTEM // QUANT-ANALYSIS TOOL</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# USER INPUTS (MOBILE OPTIMIZED)
# ---------------------------------------------------------
selected_name = st.selectbox(
    "AK TIE WÄHLEN",
    options=list(WATCHLIST.keys()),
    label_visibility="collapsed"
)
ticker_symbol = WATCHLIST[selected_name]

period = st.radio(
    "ZEITRAUM",
    options=["1M", "3M", "6M", "1Y"],
    horizontal=True,
    label_visibility="collapsed"
)

period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}

# ---------------------------------------------------------
# DATA FETCHING (ROBUST METHOD)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def load_stock_data(ticker, p_str):
    ticker_obj = yf.Ticker(ticker)
    df = ticker_obj.history(period=p_str)
    return df

try:
    df = load_stock_data(ticker_symbol, period_map[period])

    if df.empty or len(df) < 14:
        st.error("SYSTEMFEHLER: ZU WENIG DATENPUNKTE. BITTE SPÄTER ERNEUT VERSUCHEN.")
        st.stop()

    # Berechnungen
    latest_price = float(df["Close"].iloc[-1])
    prev_price = float(df["Close"].iloc[-2])
    change_pct = ((latest_price - prev_price) / prev_price) * 100

    # Indikatoren
    df["EMA50"] = df["Close"].ewm(span=min(50, len(df)), adjust=False).mean()
    
    # RSI (14) - Fehlerfrei kalkuliert
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(window=14, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(window=14, min_periods=1).mean()
    rs = gain / loss
    df["RSI"] = np.where(loss == 0, 100, 100 - (100 / (1 + rs)))
    current_rsi = float(df["RSI"].iloc[-1])

    # Volatilität
    returns = df["Close"].pct_change()
    volatility = float(returns.tail(20).std() * np.sqrt(252) * 100)

    # Signal Score (0 - 100)
    score = 50
    if latest_price > df["EMA50"].iloc[-1]: score += 20
    else: score -= 20
    
    if current_rsi < 30: score += 20
    elif current_rsi > 70: score -= 20
    
    if change_pct > 0: score += 10
    else: score -= 10
    
    score = max(5, min(95, score))

    # ---------------------------------------------------------
    # DISPLAY METRICS
    # ---------------------------------------------------------
    badge_class = "badge-bull" if change_pct >= 0 else "badge-bear"
    change_sign = "+" if change_pct >= 0 else ""
    
    rsi_badge_class = "badge-bear" if current_rsi > 70 else "badge-bull" if current_rsi < 30 else "badge-neu"
    rsi_text = "ÜBERKAUFT" if current_rsi > 70 else "ÜBERVERKAUFT" if current_rsi < 30 else "NEUTRAL"

    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">KURS</div>
            <div class="metric-value">{latest_price:.2f}</div>
            <div style="margin-top:4px;"><span class="badge {badge_class}">{change_sign}{change_pct:.2f}%</span></div>
        </div>
        <div class="metric-card">
            <div class="metric-label">RSI (14)</div>
            <div class="metric-value">{current_rsi:.1f}</div>
            <div style="margin-top:4px;"><span class="badge {rsi_badge_class}">{rsi_text}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # SIGNAL METER
    # ---------------------------------------------------------
    signal_text = "STARKES KAUFSIGNAL" if score >= 70 else "VERKAUFSIGNAL" if score <= 30 else "NEUTRAL / HALTEN"
    signal_color = "#10b981" if score >= 70 else "#ef4444" if score <= 30 else "#f59e0b"

    st.markdown(f"""
    <div class="signal-container">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span class="metric-label">QUANT SIGNAL SCORE</span>
            <span style="font-size:0.75rem; font-weight:800; color:{signal_color};">{signal_text} ({score}/100)</span>
        </div>
        <div style="background:#1e293b; height:8px; border-radius:4px; width:100%; overflow:hidden;">
            <div style="background:{signal_color}; width:{score}%; height:100%; border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # MOBILE INTERACTIVE CHART
    # ---------------------------------------------------------
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Kurs',
        increasing_line_color='#00f2fe',
        decreasing_line_color='#ff1744'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA50'],
        mode='lines',
        name='EMA 50',
        line=dict(color='#f59e0b', width=1.5)
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='#090e1a',
        margin=dict(l=5, r=5, t=10, b=10),
        height=280,
        showlegend=False,
        xaxis=dict(showgrid=False, rangeslider=dict(visible=False)),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', side='right')
    )

    # Konfiguration: Deaktiviert die Toolbar für echtes App-Feeling auf dem Handy
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ---------------------------------------------------------
    # ERKLÄR-BÄR ENGINE
    # ---------------------------------------------------------
    trend_state = "über" if latest_price > df["EMA50"].iloc[-1] else "unter"
    trend_desc = "Aufwärtstrend" if latest_price > df["EMA50"].iloc[-1] else "Abwärtstrend"
    
    if current_rsi > 70:
        rsi_explanation = "Der RSI-Wert ist über 70. Die Aktie ist aktuell heißgelaufen (überkauft). Kurzfristige Gewinnmitnahmen durch andere Marktteilnehmer sind sehr wahrscheinlich."
    elif current_rsi < 30:
        rsi_explanation = "Der RSI-Wert ist unter 30. Die Aktie wurde stark abverkauft (überverkauft). Dies ist oft eine Chance für eine kurzfristige technische Gegenbewegung nach oben."
    else:
        rsi_explanation = "Der RSI befindet sich im neutralen Bereich (30-70). Der Markt agiert derzeit ausgeglichen ohne extreme Panik oder Gier."

    if volatility > 35:
        planspiel_tip = "HOHE VOLATILITÄT: Diese Aktie schwankt massiv. Für das Planspiel Börse bietet dies die Chance auf sehr schnelle Renditen, birgt jedoch das Risiko, das Startkapital rasant zu verbrennen. Taktischer Einsatz empfohlen."
    else:
        planspiel_tip = "SOLIDE VOLATILITÄT: Ein vergleichsweise stabiler Wert. Ideal geeignet als sicheres Fundament für dein Planspiel-Depot, um konstantes Wachstum ohne extreme Risiken zu erzielen."

    st.markdown(f"""
    <div class="analysis-card">
        <div class="analysis-title">SYSTEMANALYSE // LERN-MODUL</div>
        
        <div class="analysis-p">
            <strong>TREND-DETEKTION:</strong> Die Aktie notiert aktuell <strong>{trend_state}</strong> ihrem gleitenden 50-Tage-Durchschnitt (EMA 50). Dies bestätigt mathematisch einen übergeordneten <strong>{trend_desc}</strong>.
        </div>
        
        <div class="analysis-p">
            <strong>MARKTDYNAMIK (RSI):</strong> {rsi_explanation}
        </div>
        
        <div class="analysis-p">
            <strong>PLANSPIEL-TAKTIK:</strong> {planspiel_tip}
        </div>
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.error("VERBINDUNGSFEHLER ZUR BÖRSE. BITTE NEU LADEN.")
