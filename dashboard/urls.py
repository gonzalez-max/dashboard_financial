from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_chart, name='stock_chart'),
    path('autocomplete/', views.autocomplete_ticker, name='autocomplete_ticker'),
]