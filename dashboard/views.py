from django.shortcuts import render
import yfinance as yf
import plotly.graph_objs as go
from django.shortcuts import render

def stock_chart(request):
    ticker = request.GET.get("ticker", "AAPL")  # Usar "AAPL" por defecto si no se ingresa nada
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1mo")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name='Cierre'))

    fig.update_layout(title=f"Precio de cierre - {ticker.upper()} (último mes)",
                      xaxis_title="Fecha",
                      yaxis_title="Precio (USD)")

    chart = fig.to_html(full_html=False)

    return render(request, "dashboard/stock_chart.html", {"chart": chart, "ticker": ticker})

