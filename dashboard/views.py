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
from datetime import datetime, timedelta
from functools import lru_cache
import concurrent.futures



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


@lru_cache(maxsize=128)
def get_company_name_cached(ticker):
    """Devuelve el nombre de la empresa usando la API de Finnhub (con caché simple)"""
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("name", "")

@lru_cache(maxsize=128)
def get_news_finnhub_cached(ticker):
    """Devuelve una lista de noticias para el ticker (con caché simple, solo últimos 10 días)"""
    today = datetime.today()
    from_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={from_date}&to={to_date}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    data = response.json()
    news_items = []
    for item in data[:5]:
        timestamp = item.get("datetime")
        fecha_legible = datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y") if timestamp else "Sin fecha"
        news_items.append({
            'title': item.get("headline"),
            'link': item.get("url"),
            'published': fecha_legible,
        })
    return news_items

def format_market_cap(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    if value >= 1e12:
        return f"{value/1e12:.2f}T"
    elif value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    else:
        return str(value)

@lru_cache(maxsize=128)
def get_yfinance_info_cached(ticker):
    """Devuelve info de yfinance para un ticker (con caché simple)"""
    info = yf.Ticker(ticker).info
    # Redondear valores a 2 decimales si existen
    price = info.get('currentPrice')
    if price is not None:
        price = round(price, 2)
    change_percent = info.get('regularMarketChangePercent')
    if change_percent is not None:
        change_percent = round(change_percent, 2)
    pe_ratio = info.get('trailingPE')
    if pe_ratio is not None:
        pe_ratio = round(pe_ratio, 2)
    website = info.get('website', '')
    domain = ''
    if website:
        domain = website.replace('http://', '').replace('https://', '').split('/')[0]
    return {
        'ticker': ticker,
        'price': price,
        'changePercent': change_percent,
        'marketCap': format_market_cap(info.get('marketCap')),
        'peRatio': pe_ratio,
        'domain': domain,
        'error': None
    }

@lru_cache(maxsize=128)
def get_yfinance_history_cached(ticker, period="1mo"):
    """Devuelve el historial de yfinance para un ticker y periodo (con caché simple)"""
    return yf.Ticker(ticker).history(period=period)

# buscador de ticker 
def stock_chart(request):
    # Obtener valores crudos
    new_tickers_raw = request.GET.get("tickers", "")
    remove_ticker = request.GET.get("remove", "").upper()
    ticker_from_get = request.GET.get("ticker", "").upper()
    timeframe = request.GET.get("period", "1mo")

    # Procesar lista de nuevos tickers desde input
    new_tickers = [t.strip().upper() for t in new_tickers_raw.split(',') if t.strip()]

    # Determinar el ticker principal
    if ticker_from_get:
        ticker = ticker_from_get
        request.session["ticker_principal"] = ticker  # Guardar en sesión
    elif new_tickers:
        ticker = new_tickers[0]
        request.session["ticker_principal"] = ticker  # Guardar en sesión
    else:
        ticker = request.session.get("ticker_principal", "AAPL")  # Usar guardado o AAPL

    # Inicializar lista de comparación en sesión si no existe
    if "compared_tickers" not in request.session:
        request.session["compared_tickers"] = []

    # Asegurarse de que solo haya strings simples en la sesión
    compared_tickers = [str(t).upper() for t in request.session["compared_tickers"] if isinstance(t, str)]

    # Remover ticker si se indicó
    if remove_ticker and remove_ticker in compared_tickers:
        compared_tickers = [t for t in compared_tickers if t != remove_ticker]
        new_tickers = [t for t in new_tickers if t != remove_ticker]  # ✅ lo quitamos del input
    # Eliminar duplicados y asegurar solo strings
    compared_tickers = list(dict.fromkeys([t for t in compared_tickers if isinstance(t, str)]))
    request.session["compared_tickers"] = compared_tickers
    request.session.modified = True

    # Agregar nuevos tickers desde el input (que no sea el principal)
    for t in new_tickers:
        if t != ticker and t not in compared_tickers and len(compared_tickers) < 5:
            compared_tickers.append(t)

    # Guardar lista actualizada en sesión (solo strings simples)
    request.session["compared_tickers"] = [str(t).upper() for t in compared_tickers if isinstance(t, str)]

    # Validar intervalo
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
        hist = get_yfinance_history_cached(ticker, "1mo")
        if hist.empty:
            raise ValueError("No se encontraron datos para ese ticker.")

        company_name = get_company_name_cached(ticker)
        news = get_news_finnhub_cached(ticker)

        # Armar la lista de tickers a comparar
        tickers_to_compare = [ticker] + compared_tickers

        # Usar ThreadPoolExecutor para obtener info de yfinance en paralelo
        comparation = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_ticker = {executor.submit(get_yfinance_info_cached, t): t for t in tickers_to_compare}
            for future in concurrent.futures.as_completed(future_to_ticker):
                t = future_to_ticker[future]
                try:
                    comparation.append(future.result())
                except Exception as e:
                    comparation.append({
                        'ticker': t,
                        'error': f"Error al obtener datos de {t}: {e}"
                    })

        # Buscar el dominio del ticker principal
        domain = ""
        for item in comparation:
            if item.get("ticker") == ticker:
                domain = item.get("domain", "")
                break

        return render(request, "dashboard/stock_chart.html", {
            "ticker": ticker,
            "interval": interval,
            "company_name": company_name,
            "news": news,
            "timeframe": timeframe,
            "comparacion": comparation,
            "tickers_input": ",".join([ticker] + compared_tickers),
            "domain": domain,  # <-- Agregado aquí
        })

    except Exception as e:
        return render(request, "dashboard/stock_chart.html", {
            "error": f"No se pudo cargar el gráfico: {str(e)}",
            "ticker": ticker,
            "interval": interval,
            "timeframe": timeframe,
            "comparacion": comparation,
            "tickers_input": ",".join([ticker] + compared_tickers)
        })
