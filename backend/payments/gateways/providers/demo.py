import uuid
from typing import Dict, Any
from ..base import PaymentGateway

class DemoBkashPayment(PaymentGateway):
    """
    Demo implementation of bKash payment gateway.
    Simulates the initiation and verification flow without real API calls.
    """

    def initiate_payment(self, amount: float, ride_id: int, user_email: str) -> Dict[str, Any]:
        """
        Simulates bKash payment initiation.
        Instead of a real URL, returns a mock success callback URL.
        """
        # In a real implementation, you would call bKash 'create' API here.
        # Credentials like app_key, app_secret would be in settings.py.
        
        mock_transaction_id = f"BK_{uuid.uuid4().hex[:8].upper()}"
        
        return {
            "status": "SUCCESS",
            "transaction_id": mock_transaction_id,
            "payment_url": f"/api/payments/demo-callback/?ride_id={ride_id}&trxID={mock_transaction_id}",
            "message": "Demo bKash payment initiated successfully."
        }

    def verify_payment(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates bKash payment verification (execute API).
        Always returns success for demo purposes.
        """
        # In a real implementation, you would call bKash 'execute' or 'query' API.
        
        trx_id = request_data.get('trxID')
        
        return {
            "status": "SUCCESS",
            "transaction_id": trx_id,
            "provider": "BKASH_DEMO",
            "message": "Payment verified successfully by bKash Demo."
        }
