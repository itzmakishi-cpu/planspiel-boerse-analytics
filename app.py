import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Seiten-Layout konfigurieren
st.set_page_config(page_title="Aktien-Analyse Dashboard", layout="wide")

st.title("📈 Professionelles Aktien-Analyse-Dashboard")

# ---------------------------------------------------------
# SIDEBAR: EINSTELLUNGEN
# ---------------------------------------------------------
st.sidebar.header("Einstellungen")

# 1. Jede Aktie suchen/eingeben
ticker_input = st.sidebar.text_input(
    "Ticker-Symbol eingeben:", 
    value="AAPL",
    help="Gib ein beliebiges Symbol ein (z. B. AAPL, NVDA, TSLA, MSFT oder SAP.DE für deutsche Aktien)."
).upper().strip()

# 2. Zeiträume definieren (1 Tag, 1 Woche, 1 Monat, 1 Jahr, 3 Jahre)
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
            st.error(f"Keine Daten für '{ticker_input}' gefunden. Überprüfe das Ticker-Symbol.")
        else:
            # Unternehmensname abrufen
            info = stock.info
            company_name = info.get('longName', ticker_input)

            st.subheader(f"{company_name} ({ticker_input}) — Zeitraum: {selected_tf}")

            # Indikatoren berechnen: SMA 20 & SMA 50
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()

            # Relative Strength Index (RSI) berechnen
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Key Performance Indicators (KPIs)
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
            # 3. ERWEITERTE GRAFIK (Candlestick + Moving Averages + Volumen)
            # ---------------------------------------------------------
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.08, 
                row_heights=[0.75, 0.25],
                subplot_titles=("Kursverlauf (Kerzenchart) mit Durchschnitten", "Handelsvolumen")
            )

            # Candlestick Chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Kurs (OHLC)"
            ), row=1, col=1)

            # Gleitende Durchschnitte hinzufügen
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20 (Kurzfristig)',
                line=dict(color='orange', width=1.5)
            ), row=1, col=1)

            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50 (Mittelfristig)',
                line=dict(color='deepskyblue', width=1.5)
            ), row=1, col=1)

            # Volumen Chart mit Farbkodierung (Grün/Rot)
            volume_colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' for i in range(len(df))]
            fig.add_trace(go.Bar(
                x=df.index, y=df['Volume'], name="Volumen", marker_color=volume_colors
            ), row=2, col=1)

            # Style-Anpassungen
            fig.update_layout(
                height=650,
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

            # ---------------------------------------------------------
            # 4. KAUFEINSCHÄTZUNG & BEGRÜNDUNG
            # ---------------------------------------------------------
            st.markdown("### 💡 Signal-Analyse & Begründung")

            latest_rsi = df['RSI'].iloc[-1] if not np.isnan(df['RSI'].iloc[-1]) else 50
            latest_sma20 = df['SMA_20'].iloc[-1]
            latest_sma50 = df['SMA_50'].iloc[-1]

            reasons = []
            score = 0  # Punktesystem für Kaufsignal

            # 1. Kriterium: Trend gegenüber SMA 20
            if latest_close > latest_sma20:
                reasons.append("🟢 **Positiver Kurzfrist-Trend:** Der aktuelle Kurs liegt über dem 20-Tage-Durchschnitt (SMA 20).")
                score += 1
            else:
                reasons.append("🔴 **Negativer Kurzfrist-Trend:** Der Kurs liegt unter dem 20-Tage-Durchschnitt (SMA 20), was auf Abwärtsdruck hinweist.")
                score -= 1

            # 2. Kriterium: Trend gegenüber SMA 50
            if latest_close > latest_sma50:
                reasons.append("🟢 **Starke Basis:** Der Kurs behauptet sich über dem 50-Tage-Durchschnitt (SMA 50).")
                score += 1
            else:
                reasons.append("🔴 **Schwächephase:** Der Kurs verharrt unter dem 50-Tage-Durchschnitt (SMA 50).")
                score -= 1

            # 3. Kriterium: RSI (Overbought/Oversold)
            if latest_rsi < 30:
                reasons.append(f"🟢 **Überverkauft (RSI = {latest_rsi:.1f}):** Der Relative-Stärke-Index liegt unter 30. Die Aktie ist historisch günstig/überverkauft – oft Gegenbewegung nach oben möglich.")
                score += 1.5
            elif latest_rsi > 70:
                reasons.append(f"🔴 **Überkauft (RSI = {latest_rsi:.1f}):** Der RSI liegt über 70. Die Aktie ist stark gestiegen – erhöhtes Risiko für Gewinnmitnahmen/Rücksetzer.")
                score -= 1.5
            else:
                reasons.append(f"⚪ **Neutraler RSI (RSI = {latest_rsi:.1f}):** Der Momentum-Indikator liegt im ausgeglichenen Bereich (zwischen 30 und 70).")

            # Fazit ausgeben
            if score >= 1.5:
                st.success("**Gesamteinschätzung: KAUFEN / BULLISCH**")
            elif score <= -1.5:
                st.error("**Gesamteinschätzung: VERKAUFEN / BÄRISCH**")
            else:
                st.warning("**Gesamteinschätzung: HALTEN / NEUTRAL**")

            st.write("**Warum dieses Ergebnis?**")
            for r in reasons:
                st.markdown(f"- {r}")

    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
