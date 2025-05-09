from django.shortcuts import render
import yfinance as yf
import plotly.graph_objects as go

def stock_chart(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    timeframe = request.GET.get("period", "1mo")

    # Configurar temporalidades con su periodo + intervalo
    timeframe_config = {
        "1d": {"period": "1y", "interval": "1d"},    # Velas diarias para un mes
        "1mo": {"period": "5y", "interval": "1mo"},   # Velas mensuales para un año
        "1y": {"period": "10y", "interval": "1mo"}     # Velas mensuales para cinco años
    }

    if timeframe not in timeframe_config:
        timeframe = "1mo"  # Valor por defecto

    config = timeframe_config[timeframe]

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=config["period"], interval=config["interval"])

        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker o período.")

        if hasattr(hist.index, 'tz_convert'):
            hist.index = hist.index.tz_localize(None)

        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close']
        )])

        fig.update_layout(
            title=f"Gráfico de Velas - {ticker} ({timeframe})",
            xaxis_title="Fecha",
            yaxis_title="Precio (USD)",
            xaxis_rangeslider_visible=False
        )

        chart = fig.to_html(full_html=False)
        return render(request, "dashboard/stock_chart.html", {
            "chart": chart,
            "ticker": ticker,
            "timeframe": timeframe
        })

    except Exception as e:
        return render(request, "dashboard/stock_chart.html", {
            "error": f"No se pudo cargar el gráfico: {str(e)}",
            "ticker": ticker,
            "timeframe": timeframe
        })
