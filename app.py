import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 1. STREAMLIT SEITEN-KONFIGURATION
st.set_page_config(
    page_title="Aktien & Verhaltens-Analyse",
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
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        .block-container {
            padding-top: 0.8rem !important;
            padding-bottom: 1.2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            max-width: 100% !important;
        }

        div[data-testid="stMetric"] {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 8px 12px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        div[role="radiogroup"] {
            justify-content: center;
            gap: 4px;
            width: 100%;
            margin-bottom: 8px;
        }
        div[role="radiogroup"] > label {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 18px !important;
            padding: 4px 10px !important;
            font-size: 0.8rem !important;
            color: #c9d1d9;
        }

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

# 4. SELEKTION
st.markdown("### Aktien-Analyse")
selected_stock_label = st.selectbox(
    "Aktie auswählen", 
    list(STOCK_DICT.keys()), 
    label_visibility="collapsed"
)
ticker_input = STOCK_DICT[selected_stock_label]

chart_container = st.container()

# 5. BEDIENELEMENTE (Zeitraum & Chart-Typ)
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

chart_type = st.radio(
    "Ansicht", 
    ["Linie", "Candlestick"], 
    index=0, 
    horizontal=True, 
    label_visibility="collapsed"
)

# 6. DATEN VERARBEITEN
with st.spinner("Lade Daten..."):
    stock = yf.Ticker(ticker_input)
    df = stock.history(period=period, interval=interval)

if df.empty:
    st.error(f"[FEHLER] Keine Daten für {ticker_input} verfügbar.")
else:
    # Metriken berechnen
    latest_close = df['Close'].iloc[-1]
    first_close = df['Close'].iloc[0]
    price_change = latest_close - first_close
    pct_change = (price_change / first_close) * 100

    support_level = df['Low'].min()
    resistance_level = df['High'].max()

    kpi_col1, kpi_col2 = st.columns(2)
    kpi_col1.metric("Aktueller Kurs", f"{latest_close:.2f} USD")
    kpi_col2.metric("Veränderung", f"{price_change:+.2f} USD", f"{pct_change:+.2f}%")

    # ---------------------------------------------------------
    # ANALYSE-VARIABLEN BERECHNEN
    # ---------------------------------------------------------
    lookback = min(5, len(df) - 1)
    if lookback > 0:
        recent_move = (df['Close'].iloc[-1] - df['Close'].iloc[-1 - lookback]) / df['Close'].iloc[-1 - lookback]
    else:
        recent_move = 0.0

    df['Move_N'] = df['Close'].pct_change(lookback)
    df['Future_Move_N'] = df['Close'].pct_change(lookback).shift(-lookback)

    historical_data = df.iloc[:-lookback*2].copy() if len(df) > lookback*2 else df.copy()
    tolerance = 0.025
    matches = historical_data[
        (historical_data['Move_N'] >= recent_move - tolerance) & 
        (historical_data['Move_N'] <= recent_move + tolerance)
    ]

    match_count = len(matches)
    if match_count > 0:
        positive_outcomes = (matches['Future_Move_N'] > 0).sum()
        success_rate = (positive_outcomes / match_count) * 100
        avg_future_return = matches['Future_Move_N'].mean() * 100
    else:
        success_rate = 50.0
        avg_future_return = 0.0

    df['Is_Up_Day'] = df['Close'] > df['Open']
    up_volume = df[df['Is_Up_Day']]['Volume'].sum()
    down_volume = df[~df['Is_Up_Day']]['Volume'].sum()
    total_volume = up_volume + down_volume

    buying_ratio = (up_volume / total_volume) * 100 if total_volume > 0 else 50.0
    dist_to_support_pct = ((latest_close - support_level) / support_level) * 100

    # ---------------------------------------------------------
    # 7. CHART AUFBAUEN
    # ---------------------------------------------------------
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.78, 0.22])

    # Dynamische Farbgebung für die cleane Linie basierend auf der Gesamt-Performance
    if pct_change >= 0:
        line_color = '#26a69a'  # Gruen
        fill_color = 'rgba(38, 166, 154, 0.12)'
    else:
        line_color = '#ef5350'  # Rot
        fill_color = 'rgba(239, 83, 80, 0.12)'

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Kurs", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
        ), row=1, col=1)
    else:
        # Cleane Linie mit dynamischen Farben und Schattierung
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Close'],
            mode='lines', name='Kurs',
            line=dict(color=line_color, width=2.5),
            fill='tozeroy',
            fillcolor=fill_color,
            connectgaps=True
        ), row=1, col=1)

    # Unterstützung (Gruen) & Widerstand (Rot)
    fig.add_trace(go.Scatter(
        x=[df.index[0], df.index[-1]], y=[support_level, support_level],
        mode='lines', name='Unterstützung', line=dict(color='#81c784', width=1.5, dash='dot')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=[df.index[0], df.index[-1]], y=[resistance_level, resistance_level],
        mode='lines', name='Widerstand', line=dict(color='#e57373', width=1.5, dash='dot')
    ), row=1, col=1)

    # Volumen
    volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
    ), row=2, col=1)

    fig.update_layout(
        height=420,
        template="plotly_dark",
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        dragmode=False  # Reines Durchscrollen der Seite ohne Verhakung im Chart
    )

    fig.update_xaxes(fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, showgrid=True, gridcolor='rgba(255,255,255,0.08)')

    with chart_container:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})

    # ---------------------------------------------------------
    # 8. DIE 3 ENTSCHEIDUNGSPUNKTE
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Entscheidungs-Metriken")

    if match_count > 0:
        if success_rate > 55:
            st.success(f"[1] MUSTER-ANALYSE: POSITIV\n\nÄhnliche Bewegungen gab es {match_count}-mal. In {success_rate:.0f}% der Fälle folgte ein Anstieg (Durchschnittlich {avg_future_return:+.1f}%).")
        elif success_rate < 45:
            st.error(f"[1] MUSTER-ANALYSE: NEGATIV\n\nÄhnliche Bewegungen gab es {match_count}-mal. In nur {success_rate:.0f}% der Fälle erholte sich der Kurs danach.")
        else:
            st.warning(f"[1] MUSTER-ANALYSE: NEUTRAL\n\nDie Historie zeigt keine klare Richtung bei diesem Muster ({success_rate:.0f}% Erfolgsquote).")
    else:
        st.info("[1] MUSTER-ANALYSE: UNBEKANNT\n\nKeine exakten historischen Parallelen für diese exakte Bewegung gefunden.")

    if buying_ratio > 55:
        st.success(f"[2] ANLEGER-PSYCHOLOGIE: POSITIV\n\nKaufdruck dominiert. {buying_ratio:.0f}% des Volumens entstand an steigenden Tagen. Anleger kaufen gezielt nach.")
    elif buying_ratio < 45:
        st.error(f"[2] ANLEGER-PSYCHOLOGIE: NEGATIV\n\nVerkaufsdruck dominiert. {100 - buying_ratio:.0f}% des Volumens entstand an fallenden Tagen. Anleger springen ab.")
    else:
        st.warning(f"[2] ANLEGER-PSYCHOLOGIE: NEUTRAL\n\nKauf- und Verkaufsdruck halten sich die Waage ({buying_ratio:.0f}% Käuferanteil).")

    if dist_to_support_pct < 3.0:
        st.success(f"[3] ZONEN-ABSTAND: POSITIV\n\nKurs ist nahe der Unterstützungslinie bei {support_level:.2f} USD. Starke Chance für Schnäppchenjäger.")
    elif latest_close >= resistance_level * 0.98:
        st.error(f"[3] ZONEN-ABSTAND: NEGATIV\n\nKurs ist am oberen Widerstand bei {resistance_level:.2f} USD. Gefahr von starken Gewinnmitnahmen.")
    else:
        st.warning(f"[3] ZONEN-ABSTAND: NEUTRAL\n\nKurs bewegt sich im unsicheren Mittelfeld (Abstand zur Untergrenze: {dist_to_support_pct:.1f}%).")
