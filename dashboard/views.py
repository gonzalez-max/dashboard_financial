from django.shortcuts import render
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

# Cargamos variables de entorno
load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def get_company_name(ticker):
    """Devuelve el nombre de la empresa usando la API de Finnhub"""
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("name", "")  # Devuelve "" si no encuentra nombre


def get_news_finnhub(ticker):
    """Devuelve una lista de noticias para el ticker"""
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2023-01-01&to=2025-12-31&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    news_items = []
    for item in data[:5]:  # Solo las primeras 5 noticias
        news_items.append({
            'title': item.get("headline"),
            'link': item.get("url"),
            'published': item.get("datetime"),
        })

    return news_items


def stock_chart(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    timeframe = request.GET.get("period", "1mo")

    interval_map = {
        "1d": "D",
        "1wk": "W",
        "1mo": "M",
        "1y": "D",
    }

    if timeframe not in interval_map:
        timeframe = "1mo"

    interval = interval_map[timeframe]

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")

        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker.")

        # Obtenemos nombre y noticias desde Finnhub
        company_name = get_company_name(ticker)
        news = get_news_finnhub(ticker)

        return render(request, "dashboard/stock_chart.html", {
            "ticker": ticker,
            "interval": interval,
            "company_name": company_name,
            "news": news,
            "timeframe": timeframe
        })

    except Exception as e:
        return render(request, "dashboard/stock_chart.html", {
            "error": f"No se pudo cargar el gráfico: {str(e)}",
            "ticker": ticker,
            "interval": interval,
            "timeframe": timeframe,
        })