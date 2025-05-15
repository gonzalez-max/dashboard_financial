from django.shortcuts import render
import yfinance as yf
import feedparser  # Importamos feedparser


def get_news(ticker):
    # Noticias de Google News en español para el ticker + "acciones"
    feed_url = f"https://news.google.com/rss/search?q={ticker}+acciones&hl=es-419&gl=AR&ceid=AR:es"
    news_feed = feedparser.parse(feed_url)

    news_items = []
    for entry in news_feed.entries[:5]:
        news_items.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.published
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
        company_name = stock.info.get("longName", "")

        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker.")

        # Obtenemos las noticias
        news = get_news(ticker)

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
