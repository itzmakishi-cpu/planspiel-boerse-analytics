import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Seiten-Layout konfigurieren
st.set_page_config(page_title="Aktien-Analyse Dashboard", layout="wide")

st.title("Aktien-Analyse Dashboard")

# ---------------------------------------------------------
# SIDEBAR: EINSTELLUNGEN
# ---------------------------------------------------------
st.sidebar.header("Einstellungen")

# 1. Vordefinierte Aktienliste zur einfachen Auswahl
STOCK_DICT = {
    "NVIDIA Corporation (NVDA)": "NVDA",
    "Apple Inc. (AAPL)": "AAPL",
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
    "Volkswagen AG (VOW3.DE)": "VOW3.DE",
    "-- Eigene Eingabe --": "CUSTOM"
}

selected_stock_label = st.sidebar.selectbox("Aktie auswählen:", list(STOCK_DICT.keys()))

if STOCK_DICT[selected_stock_label] == "CUSTOM":
    ticker_input = st.sidebar.text_input("Manuelles Symbol eingeben (z. B. AMD):", value="AMD").upper().strip()
else:
    ticker_input = STOCK_DICT[selected_stock_label]

# 2. Zeiträume definieren
timeframe_options = {
    "1 Tag": ("1d", "5m"),
    "1 Woche": ("5d", "15m"),
    "1 Monat": ("1mo", "1d"),
    "1 Jahr": ("1y", "1d"),
    "3 Jahre": ("3y", "1wk")
}

selected_tf = st.sidebar.radio("Zeitraum wählen:", list(timeframe_options.keys()), index=3)
period, interval = timeframe_options[selected_tf]

# ---------------------------------------------------------
# DATEN LADEN & VERARBEITEN
# ---------------------------------------------------------
if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        df = stock.history(period=period, interval=interval)

        if df.empty:
            st.error(f"[FEHLER] Keine Daten für Symbol '{ticker_input}' gefunden.")
        else:
            info = stock.info
            company_name = info.get('longName', ticker_input)

            st.subheader(f"{company_name} [{ticker_input}] — Zeitraum: {selected_tf}")

            # Indikatoren berechnen: SMA 20 & SMA 50
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()

            # Relative Strength Index (RSI)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # KPIs
            latest_close = df['Close'].iloc[-1]
            first_close = df['Close'].iloc[0]
            price_change = latest_close - first_close
            pct_change = (price_change / first_close) * 100

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Aktueller Kurs", f"{latest_close:.2f} USD")
            m2.metric("Veränderung im Zeitraum", f"{price_change:+.2f} USD", f"{pct_change:+.2f}%")
            m3.metric("Höchstkurs", f"{df['High'].max():.2f} USD")
            m4.metric("Tiefstkurs", f"{df['Low'].min():.2f} USD")

            # ---------------------------------------------------------
            # 3. GRAFIK (Candlestick + Moving Averages + Volumen)
            # ---------------------------------------------------------
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.08, 
                row_heights=[0.75, 0.25],
                subplot_titles=("Kursverlauf (Candlestick) & Durchschnitte", "Handelsvolumen")
            )

            # Candlestick Chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Kurs (OHLC)"
            ), row=1, col=1)

            # SMA Lines
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20 (Kurzfristig)',
                line=dict(color='orange', width=1.5)
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50 (Mittelfristig)',
                line=dict(color='deepskyblue', width=1.5)
            ), row=1, col=1)

            # Volumen Chart
            volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
            fig.add_trace(go.Bar(
                x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
            ), row=2, col=1)

            # Layout Styling
            fig.update_layout(
                height=650,
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

            # ---------------------------------------------------------
            # 4. SIGNAL-ANALYSE & BEGRÜNDUNG
            # ---------------------------------------------------------
            st.markdown("### Signal-Analyse & Begründung")

            latest_rsi = df['RSI'].iloc[-1] if not np.isnan(df['RSI'].iloc[-1]) else 50
            latest_sma20 = df['SMA_20'].iloc[-1]
            latest_sma50 = df['SMA_50'].iloc[-1]

            reasons = []
            score = 0

            # Kriterium 1: SMA 20
            if latest_close > latest_sma20:
                reasons.append("[+] **Positiver Kurzfrist-Trend:** Der aktuelle Kurs liegt über dem 20-Tage-Durchschnitt (SMA 20).")
                score += 1
            else:
                reasons.append("[-] **Negativer Kurzfrist-Trend:** Der Kurs liegt unter dem 20-Tage-Durchschnitt (SMA 20).")
                score -= 1

            # Kriterium 2: SMA 50
            if latest_close > latest_sma50:
                reasons.append("[+] **Starke Basis:** Der Kurs behauptet sich über dem 50-Tage-Durchschnitt (SMA 50).")
                score += 1
            else:
                reasons.append("[-] **Schwächephase:** Der Kurs verharrt unter dem 50-Tage-Durchschnitt (SMA 50).")
                score -= 1

            # Kriterium 3: RSI
            if latest_rsi < 30:
                reasons.append(f"[+] **Überverkauft (RSI = {latest_rsi:.1f}):** Der Wert liegt unter 30. Historisch günstige Situation / Erholungspotenzial vorhanden.")
                score += 1.5
            elif latest_rsi > 70:
                reasons.append(f"[-] **Überkauft (RSI = {latest_rsi:.1f}):** Der Wert liegt über 70. Gewinne wurden stark ausgereizt / erhöhtes Korrekturrisiko.")
                score -= 1.5
            else:
                reasons.append(f"[i] **Neutraler RSI (RSI = {latest_rsi:.1f}):** Der Momentum-Indikator liegt im ausgeglichenen Bereich (zwischen 30 und 70).")

            # Fazit
            if score >= 1.5:
                st.success("[SIGNAL: KAUFEN / BULLISCH]")
            elif score <= -1.5:
                st.error("[SIGNAL: VERKAUFEN / BÄRISCH]")
            else:
                st.warning("[SIGNAL: HALTEN / NEUTRAL]")

            st.write("**Begründung der Analyse:**")
            for r in reasons:
                st.markdown(f"- {r}")

    except Exception as e:
        st.error(f"[FEHLER] Fehler bei der Datenverarbeitung: {e}")
