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
st.markdown("### Aktien- & Verhaltens-Analyse")
selected_stock_label = st.selectbox(
    "Aktie auswählen", 
    list(STOCK_DICT.keys()), 
    label_visibility="collapsed"
)
ticker_input = STOCK_DICT[selected_stock_label]

# Chart-Container
chart_container = st.container()

# 5. ZEITRAUM-AUSWAHL
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

# 6. DATEN VERARBEITEN
with st.spinner("Lade Daten und analysiere Verhaltensmuster..."):
    stock = yf.Ticker(ticker_input)
    df = stock.history(period=period, interval=interval)

if df.empty:
    st.error(f"[FEHLER] Keine Daten für {ticker_input} verfügbar.")
else:
    # Basic Metrics
    latest_close = df['Close'].iloc[-1]
    first_close = df['Close'].iloc[0]
    price_change = latest_close - first_close
    pct_change = (price_change / first_close) * 100

    # Key Level (Unterstützung & Widerstand)
    support_level = df['Low'].min()
    resistance_level = df['High'].max()

    # Metrics Display (2x2 Grid)
    kpi_col1, kpi_col2 = st.columns(2)
    kpi_col1.metric("Aktueller Kurs", f"{latest_close:.2f} USD")
    kpi_col2.metric("Veränderung", f"{price_change:+.2f} USD", f"{pct_change:+.2f}%")

    kpi_col3, kpi_col4 = st.columns(2)
    kpi_col3.metric("Unterstützung (Tief)", f"{support_level:.2f} USD")
    kpi_col4.metric("Widerstand (Hoch)", f"{resistance_level:.2f} USD")

    # ---------------------------------------------------------
    # HISTORISCHER MUSTER-VERGLEICH (Pattern Matching)
    # ---------------------------------------------------------
    lookback = min(5, len(df) - 1)
    if lookback > 0:
        recent_move = (df['Close'].iloc[-1] - df['Close'].iloc[-1 - lookback]) / df['Close'].iloc[-1 - lookback]
    else:
        recent_move = 0.0

    # Wir durchsuchen die Kurshistorie nach ähnlichen Bewegungen (+/- 2.5%)
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

    # ---------------------------------------------------------
    # MARKT-PSYCHOLOGIE & VOLUMEN-ANALYSE
    # ---------------------------------------------------------
    df['Is_Up_Day'] = df['Close'] > df['Open']
    up_volume = df[df['Is_Up_Day']]['Volume'].sum()
    down_volume = df[~df['Is_Up_Day']]['Volume'].sum()
    total_volume = up_volume + down_volume

    if total_volume > 0:
        buying_ratio = (up_volume / total_volume) * 100
    else:
        buying_ratio = 50.0

    # Distance to Support
    dist_to_support_pct = ((latest_close - support_level) / support_level) * 100

    # ---------------------------------------------------------
    # 7. CHART AUFBAUEN
    # ---------------------------------------------------------
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

    # Unterstützungslinie (Support)
    fig.add_trace(go.Scatter(
        x=[df.index[0], df.index[-1]], y=[support_level, support_level],
        mode='lines', name='Unterstützung',
        line=dict(color='#81c784', width=1.5, dash='dot')
    ), row=1, col=1)

    # Widerstandslinie (Resistance)
    fig.add_trace(go.Scatter(
        x=[df.index[0], df.index[-1]], y=[resistance_level, resistance_level],
        mode='lines', name='Widerstand',
        line=dict(color='#e57373', width=1.5, dash='dot')
    ), row=1, col=1)

    # Volumen
    volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
    ), row=2, col=1)

    # Layout Anpassungen
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

    fig.update_xaxes(fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, showgrid=True, gridcolor='rgba(255,255,255,0.08)')

    # Chart rendern
    with chart_container:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ---------------------------------------------------------
    # 8. AUSWERTUNG: HISTORIE + PSYCHOLOGIE + SIGNAL
    # ---------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Historie & Anleger-Verhalten")

    # Gesamteinschätzung berechnen
    overall_score = 0

    if success_rate > 55:
        overall_score += 1
    elif success_rate < 45:
        overall_score -= 1

    if buying_ratio > 55:
        overall_score += 1
    elif buying_ratio < 45:
        overall_score -= 1

    if dist_to_support_pct < 3.0:
        # Nah an der Unterstützung -> Schnäppchenjäger-Zone
        overall_score += 1

    # Signal-Ausgabe
    if overall_score >= 1:
        st.success("[SIGNAL: KAUFEN / DIP-BUYING POTENZIAL]")
    elif overall_score <= -1:
        st.error("[SIGNAL: VERKAUFEN / ABWÄRTSDRUCK]")
    else:
        st.warning("[SIGNAL: HALTEN / ABWARTEN]")

    # Detail-Analyse
    st.markdown(f"**[MUSTER-ANALYSE] Ist diese Situation schon vorgekommen?**")
    if match_count > 0:
        st.markdown(
            f"- Ähnliche Kursbewegungen ({recent_move:+.1%}) wurden in der Historie dieser Aktie **{match_count}-mal** identifiziert.\n"
            f"- In **{success_rate:.0f}% der Fälle** folgte daraufhin eine Kurserholung.\n"
            f"- Die durchschnittliche Rendite in den Folgeperioden lag bei **{avg_future_return:+.1f}%**."
        )
    else:
        st.markdown("- Für diese spezifische Kurzfrist-Bewegung wurden keine exakten historischen Parallelen im gewählten Zeitraum gefunden.")

    st.markdown(f"**[ANLEGER-PSYCHOLOGIE] Einsteigen oder Abspringen?**")
    if buying_ratio > 55:
        st.markdown(f"- **Kaufdruck dominiert ({buying_ratio:.0f}% Akkumulation):** Höheres Volumen an steigenden Tagen zeigt, dass Anleger gezielt einsteigen und Rücksetzer aufkaufen.")
    elif buying_ratio < 45:
        st.markdown(f"- **Verkaufsdruck dominiert ({100 - buying_ratio:.0f}% Distribution):** Anleger ziehen Kapital ab. Bei Kursrücksetzern droht Panik, da Marktteilnehmer eher abspringen als nachzukaufen.")
    else:
        st.markdown(f"- **Ausgeglichene Lage ({buying_ratio:.0f}% Kaufvolumen):** Käufer und Verkäufer halten sich derzeit die Waage.")

    if dist_to_support_pct < 3.0:
        st.markdown(f"- **Unterstützungszone nah ({latest_close:.2f} USD):** Der Kurs testet eine historische Untergrenze. Hier steigen erfahrungsgemäß Schnäppchenjäger ein, um von Gegenbewegungen zu profitieren.")
    elif latest_close >= resistance_level * 0.98:
        st.markdown(f"- **Widerstandszone erreicht ({resistance_level:.2f} USD):** Der Kurs ist nahe dem Höchststand. Hier neigen Anleger zu Gewinnmitnahmen, weshalb Verkaufsdruck entstehen kann.")

    st.markdown("""
    **Legende zur Grafik:**
    - **Gruene / Rote Kerzen:** Aktueller Kursverlauf (Eröffnung, Hoch, Tief, Schluss).
    - **Gepunktete gruene Linie:** Historische Unterstützung (Kaufzone).
    - **Gepunktete rote Linie:** Historischer Widerstand (Verkaufszone).
    - **Balken unten:** Gehandeltes Volumen (Grün = Kaufvolumen, Rot = Verkaufsvolumen).
    """)
