from django.conf import settings
from .providers.demo import DemoBkashPayment
from .providers.cash import CashPayment

class PaymentGatewayFactory:
    """
    Factory to return the configured payment gateway provider.
    This allows switching between Demo, bKash, SSLCommerz without
    changing core business logic.
    """

    @staticmethod
    def get_gateway(provider_name=None):
        if not provider_name:
            provider_name = getattr(settings, 'PAYMENT_PROVIDER', 'DEMO')

        if provider_name == 'DEMO':
            return DemoBkashPayment()
        
        if provider_name == 'CASH':
            return CashPayment()
        
        # New gateways are added here
        # elif provider_name == 'BKASH_REAL':
        #     return BkashRealPayment()
        
        raise ValueError(f"Unknown payment provider: {provider_name}")
