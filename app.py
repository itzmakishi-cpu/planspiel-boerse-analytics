import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# 1. APP-LAYOUT & DESIGN (Clean Look)
st.set_page_config(page_title="Aktien Dashboard", layout="wide", initial_sidebar_state="collapsed")

# CSS für einen saubereren "Real App"-Look (versteckt Standard-Streamlit-Elemente)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 2. AKTIEN-DATENBANK (Feste Auswahl)
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

# 3. KOPFZEILE & AUSWAHL (Zentral im Hauptfenster)
st.markdown("### Aktien-Analyse & Prognose")
selected_stock_label = st.selectbox("Wähle eine Aktie aus der Liste:", list(STOCK_DICT.keys()), label_visibility="collapsed")
ticker_input = STOCK_DICT[selected_stock_label]

# Chart-Container vorab erstellen (damit wir den Zeitraum-Schalter darunter platzieren können)
chart_container = st.container()

# 4. ZEITRAUM-AUSWAHL (Direkt unter dem Chart als flache Leiste)
st.write("") # Abstand
col_space1, col_center, col_space2 = st.columns([1, 3, 1])
with col_center:
    timeframe_options = {
        "1 Tag": ("1d", "5m"),
        "1 Woche": ("5d", "15m"),
        "1 Monat": ("1mo", "1d"),
        "1 Jahr": ("1y", "1d"),
        "3 Jahre": ("3y", "1wk")
    }
    # Horizontaler Radio-Button für App-ähnliche Bedienung
    selected_tf = st.radio("Zeitraum", list(timeframe_options.keys()), index=3, horizontal=True, label_visibility="collapsed")
    period, interval = timeframe_options[selected_tf]

# 5. DATEN LADEN & BERECHNEN
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

    # KPIs ganz oben anzeigen
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aktueller Kurs", f"{latest_close:.2f} USD")
    col2.metric("Veränderung", f"{price_change:+.2f} USD", f"{pct_change:+.2f}%")
    col3.metric("Tief (Zeitraum)", f"{df['Low'].min():.2f} USD")
    col4.metric("Hoch (Zeitraum)", f"{df['High'].max():.2f} USD")

    # Trend-Prognose berechnen (Lineare Regression)
    x_vals = np.arange(len(df))
    y_vals = df['Close'].values
    z = np.polyfit(x_vals, y_vals, 1) # 1. Grades = Lineare Linie
    p = np.poly1d(z)
    
    # Zukunftspunkte generieren (ca. 10% des Zeitraums in die Zukunft)
    proj_len = max(5, len(df) // 10)
    x_proj = np.arange(len(df) - 1, len(df) + proj_len)
    y_proj = p(x_proj)
    
    avg_delta = (df.index[-1] - df.index[0]) / len(df)
    future_dates = [df.index[-1] + avg_delta * i for i in range(0, proj_len + 1)]

    # 6. GRAFIK AUFBAUEN (Plotly)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.8, 0.2]
    )

    # A) Kerzenchart
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Kurs", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=1)

    # B) Historischer Trend
    fig.add_trace(go.Scatter(
        x=df.index, y=p(x_vals), mode='lines', name='Bisheriger Trend',
        line=dict(color='rgba(255, 255, 255, 0.3)', width=2, dash='dash')
    ), row=1, col=1)

    # C) Zukunfts-Prognose (Wahrscheinlicher Verlauf)
    fig.add_trace(go.Scatter(
        x=future_dates, y=y_proj, mode='lines', name='Prognostizierter Verlauf',
        line=dict(color='#ffb74d', width=3, dash='dot')
    ), row=1, col=1)

    # D) Volumen
    volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
    ), row=2, col=1)

    # 7. GRAFIK "APP-LIKE" KONFIGURIEREN (Kein Zoom, clean)
    fig.update_layout(
        height=550,
        template="plotly_dark",
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False, # Ausblenden für cleaneren Look, Hover zeigt alles
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # Zoom und Panning deaktivieren, nur Hover erlauben
    fig.update_xaxes(fixedrange=True, showgrid=False)
    fig.update_yaxes(fixedrange=True, showgrid=True, gridcolor='rgba(255,255,255,0.1)')

    # Chart im vorher definierten Container anzeigen (Menu Bar deaktiviert)
    with chart_container:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 8. ANALYSE & ERKLÄRUNG
    st.markdown("---")
    st.markdown("#### Einschätzung & Verlauf")

    # Prognose-Richtung auswerten
    trend_slope = z[0] # Steigung der Trendlinie
    
    if trend_slope > 0:
        trend_text = f"[+] **Positiver Ausblick:** Die gestrichelte orange Linie in der Grafik zeigt die mathematische Prognose. Wenn das aktuelle Momentum anhält, ist in absehbarer Zeit mit einem weiteren Kursanstieg in Richtung **{y_proj[-1]:.2f} USD** zu rechnen."
        signal = "[SIGNAL: KAUFEN]"
        signal_color = "success"
    elif trend_slope < 0:
        trend_text = f"[-] **Negativer Ausblick:** Die gestrichelte orange Linie (Prognose) zeigt nach unten. Hält der aktuelle Druck an, könnte der Kurs weiter in Richtung **{y_proj[-1]:.2f} USD** abrutschen. Vorsicht ist geboten."
        signal = "[SIGNAL: VERKAUFEN]"
        signal_color = "error"
    else:
        trend_text = "[i] **Seitwärtsphase:** Die Trendlinie verläuft nahezu flach. Es ist aktuell mit keinen großen, eindeutigen Ausbrüchen nach oben oder unten zu rechnen."
        signal = "[SIGNAL: HALTEN]"
        signal_color = "warning"

    # Ausgabe des Signals
    if signal_color == "success":
        st.success(signal)
    elif signal_color == "error":
        st.error(signal)
    else:
        st.warning(signal)

    st.markdown(trend_text)
    
    st.markdown("""
    **Wie ist die Grafik zu lesen?**
    - **Rot/Grüne Balken (oben):** Die tatsächliche Kursentwicklung (Grün = Kurs stieg, Rot = Kurs fiel). Fährst du mit der Maus darüber, siehst du die genauen Höchst- und Tiefstwerte.
    - **Weiße gestrichelte Linie:** Der durchschnittliche Trend der Vergangenheit.
    - **Orange gepunktete Linie:** Die mathematische Fortsetzung dieses Trends in die nahe Zukunft (Prognose).
    - **Balken (unten):** Das Handelsvolumen (wie viele Aktien an diesem Zeitpunkt gehandelt wurden).
    """)
