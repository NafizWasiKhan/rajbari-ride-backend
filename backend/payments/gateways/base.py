from abc import ABC, abstractmethod
from typing import Dict, Any

class PaymentGateway(ABC):
    """
    Abstract Base Class for all payment gateways.
    New gateways (like bKash, SSLCommerz) must inherit from this and 
    implement initiate and verify methods.
    """

    @abstractmethod
    def initiate_payment(self, amount: float, ride_id: int, user_email: str) -> Dict[str, Any]:
        """
        Initiates a payment with the provider.
        Returns a dictionary with status and redirect_url (if applicable).
        """
        pass

    @abstractmethod
    def verify_payment(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifies a payment from callback data.
        Returns a dictionary with status (SUCCESS/FAILED) and transaction_id.
        """
        pass
