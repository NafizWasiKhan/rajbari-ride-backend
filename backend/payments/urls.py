from django.urls import path
from .views import InitiatePaymentView, PaymentCallbackView, DemoPaymentCallbackView, WalletStatsView

urlpatterns = [
    path('initiate/', InitiatePaymentView.as_view(), name='payment-initiate'),
    path('callback/', PaymentCallbackView.as_view(), name='payment-callback'),
    path('demo-callback/', DemoPaymentCallbackView.as_view(), name='payment-demo-callback'),
    path('wallet/stats/', WalletStatsView.as_view(), name='wallet-stats'),
]
