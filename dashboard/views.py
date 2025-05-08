from django.shortcuts import render
import yfinance as yf
import plotly.graph_objs as go
from django.shortcuts import render

def stock_chart(request):
    stock = yf.Ticker("AAPL")
    hist = stock.history(period="1mo")  # Último mes

    # Crear gráfico con Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], mode='lines', name='Cierre'))

    fig.update_layout(title="Precio de cierre - AAPL (último mes)",
                      xaxis_title="Fecha",
                      yaxis_title="Precio (USD)")

    # Convertir gráfico en HTML
    chart = fig.to_html(full_html=False)

    return render(request, "dashboard/stock_chart.html", {"chart": chart})
