from django.shortcuts import render

def stock_chart(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    timeframe = request.GET.get("period", "1mo")

    # Mapeo para intervalos compatibles con TradingView
    interval_map = {
        "1d": "D",
        "1wk": "W",
        "1mo": "M",
        "1y": "D",  # Podés usar "W" también si preferís
    }

    if timeframe not in interval_map:
        timeframe = "1mo"

    interval = interval_map[timeframe]

    try:
        # Verificamos que el ticker exista mínimamente con yfinance
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")  # Consulta rápida para verificar validez
        company_name = stock.info.get("longName", "")

        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker.")

        return render(request, "dashboard/stock_chart.html", {
            "ticker": ticker,
            "interval": interval,
            "company_name": company_name,
        })

    except Exception as e:
        return render(request, "dashboard/stock_chart.html", {
            "error": f"No se pudo cargar el gráfico: {str(e)}",
            "ticker": ticker,
            "interval": interval,
        })
