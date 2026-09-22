import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 1. STREAMLIT SEITEN-KONFIGURATION
st.set_page_config(
    page_title="Aktien Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. HTML & CUSTOM CSS FOR MOBILE / HERMIT LIGHT APP
st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="theme-color" content="#0e1117">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    </head>
    <style>
        /* Streamlit Standard-Header und Footer ausblenden */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Abstände für Mobile-Displays optimieren */
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            max-width: 100% !important;
        }

        /* Styling der Metric-Karten im App-Look */
        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 8px 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        /* Touch-freundliche Zeitraum-Buttons (Pill-Design) */
        div[role="radiogroup"] {
            justify-content: center;
            gap: 4px;
            width: 100%;
        }
        div[role="radiogroup"] > label {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 18px !important;
            padding: 4px 10px !important;
            font-size: 0.8rem !important;
            color: #c9d1d9;
        }

        /* Auswahlliste (Dropdown) vergrößern für leichte Touch-Bedienung */
        div[data-baseweb="select"] {
            border-radius: 10px !important;
            border: 1px solid #30363d !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. AKTIEN-DATENBANK
STOCK_DICT = {
    "Apple Inc. (AAPL)": "AAPL",
    "NVIDIA Corporation (NVDA)": "NVDA",
    "Microsoft Corporation (MSFT)": "MSFT",
    "Tesla, Inc. (TSLA)": "TSLA",
    "Amazon.com Inc. (AMZN)": "AMZN",
    "Alphabet / Google (GOOGL)": "GOOGL",
    "Meta Platforms (META)": "META",
    "SAP SE (SAP.DE)": "SAP.DE",
    "Siemens AG (SIE.DE)": "SIE.DE",
    "Allianz SE (ALV.DE)": "ALV.DE",
    "Deutsche Telekom (DTE.DE)": "DTE.DE",
    "BMW AG (BMW.DE)": "BMW.DE",
    "Mercedes-Benz Group (MBG.DE)": "MBG.DE",
    "Volkswagen AG (VOW3.DE)": "VOW3.DE"
}

# 4. KOPFBEREICH & SELEKTION
st.markdown("### Aktien-Analyse")
selected_stock_label = st.selectbox(
    "Aktie auswählen", 
    list(STOCK_DICT.keys()), 
    label_visibility="collapsed"
)
ticker_input = STOCK_DICT[selected_stock_label]

# Chart-Container
chart_container = st.container()

# 5. ZEITRAUM-AUSWAHL (Mobiloptimierte Leiste direkt unter dem Chart)
timeframe_options = {
    "1 Tag": ("1d", "5m"),
    "1 Woche": ("5d", "15m"),
    "1 Monat": ("1mo", "1d"),
    "1 Jahr": ("1y", "1d"),
    "3 Jahre": ("3y", "1wk")
}

selected_tf = st.radio(
    "Zeitraum", 
    list(timeframe_options.keys()), 
    index=3, 
    horizontal=True, 
    label_visibility="collapsed"
)
period, interval = timeframe_options[selected_tf]

# 6. DATEN VERARBEITEN & BERECHNEN
with st.spinner("Lade..."):
    stock = yf.Ticker(ticker_input)
    df = stock.history(period=period, interval=interval)

if df.empty:
    st.error(f"[FEHLER] Keine Daten für {ticker_input} verfügbar.")
else:
    # Key Metrics
    latest_close = df['Close'].iloc[-1]
    first_close = df['Close'].iloc[0]
    price_change = latest_close - first_close
    pct_change = (price_change / first_close) * 100

    # 2x2 Grid für Smartphones (bessere Übersicht auf kleinen Bildschirmen)
    kpi_col1, kpi_col2 = st.columns(2)
    kpi_col1.metric("Aktuell", f"{latest_close:.2f} USD")
    kpi_col2.metric("Veränderung", f"{price_change:+.2f} USD", f"{pct_change:+.2f}%")

    kpi_col3, kpi_col4 = st.columns(2)
    kpi_col3.metric("Tief", f"{df['Low'].min():.2f} USD")
    kpi_col4.metric("Hoch", f"{df['High'].max():.2f} USD")

    # Trend-Prognose (Lineare Regression)
    x_vals = np.arange(len(df))
    y_vals = df['Close'].values
    z = np.polyfit(x_vals, y_vals, 1)
    p = np.poly1d(z)

    # Zukunftsprojektion
    proj_len = max(5, len(df) // 10)
    x_proj = np.arange(len(df) - 1, len(df) + proj_len)
    y_proj = p(x_proj)

    avg_delta = (df.index[-1] - df.index[0]) / len(df)
    future_dates = [df.index[-1] + avg_delta * i for i in range(0, proj_len + 1)]

    # 7. CHART ERSTELLEN (Für Smartphone Touch-Bedienung optimiert)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.04, 
        row_heights=[0.78, 0.22]
    )

    # Kerzenchart
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Kurs", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=1)

    # Bisheriger Trend
    fig.add_trace(go.Scatter(
        x=df.index, y=p(x_vals), mode='lines', name='Bisheriger Trend',
        line=dict(color='rgba(255, 255, 255, 0.3)', width=1.5, dash='dash')
    ), row=1, col=1)

    # Zukunfts-Prognose
    fig.add_trace(go.Scatter(
        x=future_dates, y=y_proj, mode='lines', name='Prognose',
        line=dict(color='#ffb74d', width=2.5, dash='dot')
    ), row=1, col=1)

    # Volumen
    volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
    ), row=2, col=1)

    # Layout Anpassungen (Höhe auf Mobile-Bildschirme abgestimmt)
    fig.update_layout(
        height=420,
        template="plotly_dark",
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    # Fixierte Achsen verhindern versehentliches Wischen/Zoomen auf dem Touchscreen
    fig.update_xaxes(fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, showgrid=True, gridcolor='rgba(255,255,255,0.08)')

    # Chart rendern
    with chart_container:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 8. ANALYSE & EVALUIERUNG
    st.markdown("---")
    st.markdown("#### Einschätzung & Verlauf")

    trend_slope = z[0]

    if trend_slope > 0:
        trend_text = f"[+] **Positiver Ausblick:** Die gestrichelte orange Linie zeigt die mathematische Prognose. Hält das Momentum an, ist kurzfristig ein Anstieg in Richtung **{y_proj[-1]:.2f} USD** realistisch."
        signal = "[SIGNAL: KAUFEN]"
        signal_type = "success"
    elif trend_slope < 0:
        trend_text = f"[-] **Negativer Ausblick:** Die Prognose zeigt nach unten. Bei anhaltendem Druck könnte der Kurs auf etwa **{y_proj[-1]:.2f} USD** fallen."
        signal = "[SIGNAL: VERKAUFEN]"
        signal_type = "error"
    else:
        trend_text = "[i] **Seitwärtsphase:** Die Trendlinie ist flach. Aktuell zeichnet sich kein starker Impuls ab."
        signal = "[SIGNAL: HALTEN]"
        signal_type = "warning"

    if signal_type == "success":
        st.success(signal)
    elif signal_type == "error":
        st.error(signal)
    else:
        st.warning(signal)

    st.markdown(trend_text)

    st.markdown("""
    **Chart-Erklärung:**
    - **Grün / Rot:** Tageskerzen (Steigend / Fallend). Bei Berührung mit dem Finger werden genaue Werte eingeblendet.
    - **Gestrichelte weiße Linie:** Historischer Durchschnittstrend.
    - **Gepunktete orange Linie:** Mathematische Zukunftsprognose.
    - **Balken unten:** Gehandeltes Volumen.
    """)
