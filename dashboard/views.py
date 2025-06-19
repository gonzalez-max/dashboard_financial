from django.shortcuts import render
import yfinance as yf
import requests
import os
from dotenv import load_dotenv
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime



#codigo de formulario
def contacto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        asunto = request.POST.get('asunto') 
        email = request.POST.get('email')
        mensaje = request.POST.get('mensaje')

        # Armamos el contenido del correo
        subject = f'{asunto} - Mensaje de {nombre}'
        message = f'Nombre: {nombre}\nCorreo: {email}\nAsunto: {asunto}\n\nMensaje:\n{mensaje}'
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [settings.CONTACT_EMAIL] 
        
        #campo oculto antibots 
        telefono = request.POST.get('telefono')
        if telefono:  # Si el bot llenó este campo oculto
                    return redirect('contacto')  # Ignoramos el envío

        # Enviamos el correo dentro de un bloque try/except
        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, '¡Tu mensaje fue enviado con éxito!')
        except Exception as e:
            # Mensaje de error para el usuario
            messages.error(request, 'Ocurrió un error al enviar el mensaje. Por favor, intenta nuevamente más tarde.')
            # Opcional: loguea el error para depuración
            print(f"Error al enviar el correo: {e}")

        return redirect('contacto')  # Redirigimos a la misma página o a otra

    return render(request, 'contact/contact.html')


#codigo de autocompletado 
def autocomplete_ticker(request):
    query = request.GET.get('query', '')
    if not query:
        return JsonResponse([], safe=False)

    url = f'https://finnhub.io/api/v1/search?q={query}&token={settings.FINNHUB_API_KEY}'
    response = requests.get(url)
    results = response.json().get('result', [])

    suggestions = [
        {
            'symbol': r['symbol'],
            'description': r['description']
        }
        for r in results if r['symbol'] and r['description']
    ]

    return JsonResponse(suggestions, safe=False)





# Cargamos variables de entorno
load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


def get_company_name(ticker):
    """Devuelve el nombre de la empresa usando la API de Finnhub"""
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("name", "")  # Devuelve "" si no encuentra nombre

# noticias 
def get_news_finnhub(ticker):
    """Devuelve una lista de noticias para el ticker"""
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2023-01-01&to=2025-12-31&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()

    news_items = []
    for item in data[:5]:  # Solo las primeras 5 noticias
        timestamp = item.get("datetime")
        fecha_legible = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y") if timestamp else "Sin fecha"

        news_items.append({
            'title': item.get("headline"),
            'link': item.get("url"),
            'published': fecha_legible,
        })

    return news_items

# buscador de ticker 
def stock_chart(request):
    ticker = request.GET.get("ticker", "AAPL").upper()
    timeframe = request.GET.get("period", "1mo")
    new_tickers_raw = request.GET.get("tickers", "")
    remove_ticker = request.GET.get("remove", "").upper()

    # Inicializamos la sesión si no existe
    if "compared_tickers" not in request.session:
        request.session["compared_tickers"] = []

    # Convertimos a lista y normalizamos
    compared_tickers = request.session["compared_tickers"]

    # Remover ticker si se indicó
    if remove_ticker and remove_ticker in compared_tickers:
        compared_tickers.remove(remove_ticker)

    # Agregar nuevos tickers desde el input (si se enviaron)
    if new_tickers_raw:
        new_tickers = [t.strip().upper() for t in new_tickers_raw.split(',') if t.strip()]
        for t in new_tickers:
            if t not in compared_tickers and len(compared_tickers) < 5:
                compared_tickers.append(t)

    # Guardamos nuevamente la sesión actualizada
    request.session["compared_tickers"] = compared_tickers

    interval_map = {
        "1d": "D",
        "1wk": "W",
        "1mo": "M",
        "1y": "D",
    }

    if timeframe not in interval_map:
        timeframe = "1mo"

    interval = interval_map[timeframe]
    comparation = []

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker.")

        # Obtenemos nombre y noticias
        company_name = get_company_name(ticker)
        news = get_news_finnhub(ticker)

        tickers_to_compare = [ticker] + compared_tickers

        for t in tickers_to_compare:
            try:
                info = yf.Ticker(t).info
                comparation.append({
                    'ticker': t,
                    'price': info.get('currentPrice'),
                    'changePercent': info.get('regularMarketChangePercent'),
                    'marketCap': info.get('marketCap'),
                    'peRatio': info.get('trailingPE'),
                    'error': None
                })
            except Exception as e:
                comparation.append({
                    'ticker': t,
                    'error': f"Error al obtener datos de {t}: {e}"
                })

        return render(request, "dashboard/stock_chart.html", {
            "ticker": ticker,
            "interval": interval,
            "company_name": company_name,
            "news": news,
            "timeframe": timeframe,
            "comparacion": comparation
        })

    except Exception as e:
        return render(request, "dashboard/stock_chart.html", {
            "error": f"No se pudo cargar el gráfico: {str(e)}",
            "ticker": ticker,
            "interval": interval,
            "timeframe": timeframe,
            "comparacion": comparation
        })
