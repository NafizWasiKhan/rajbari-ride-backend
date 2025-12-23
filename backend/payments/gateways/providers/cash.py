from typing import Dict, Any
from ..base import PaymentGateway

class CashPayment(PaymentGateway):
    """
    Implementation for Hand Cash payments.
    Simply records the intent; the actual money transfer happens offline.
    """
    provider_name = "CASH"

    def initiate_payment(self, amount: float, ride_id: int, user_email: str) -> Dict[str, Any]:
        """
        Immediately 'succeeds' since cash is handled manually.
        """
        # We simulate a successful initiation. 
        # In this case, we don't need a redirect URL, so we can return a success status
        # and handle the completion immediately in the view or via a client-side follow-up.
        return {
            "status": "SUCCESS",
            "transaction_id": f"CASH_{ride_id}",
            "message": "Hand cash payment recorded. Please pay the driver directly."
        }

    def verify_payment(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cash verify is always successful if initiated.
        """
        trx_id = request_data.get('transaction_id') or request_data.get('trxID')
        return {
            "status": "SUCCESS",
            "transaction_id": trx_id,
            "provider": "CASH",
            "message": "Cash payment verified."
        }
