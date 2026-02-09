from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('send/', views.send_money_view, name='send_money'),
    path('pay-chama/', views.pay_chama_view, name='pay_chama'),
    path('transactions/', views.transaction_history_view, name='transaction_history'),
    path('dashboard/', views.wallet_view, name='wallet_dashboard'),
]