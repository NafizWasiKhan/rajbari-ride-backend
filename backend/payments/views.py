from django.shortcuts import get_object_or_404, redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.urls import reverse

from .models import Payment
from rides.models import Ride
from .gateways.factory import PaymentGatewayFactory
from .services.payment_service import PaymentService

class InitiatePaymentView(APIView):
    """
    Kicks off the payment process using the configured gateway.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ride_id = request.data.get('ride_id')
        ride = get_object_or_404(Ride, id=ride_id, rider=request.user)
        
        if ride.status != 'COMPLETED':
            return Response({"error": "Ride must be COMPLETED before payment."}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Check for existing completed payment
        existing = Payment.objects.filter(ride=ride, status='COMPLETED').first()
        if existing:
            return Response({"error": "Ride already paid."}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Get Gateway Provider (Demo/bKash/CASH)
        method = request.data.get('method', 'DEMO')
        try:
            gateway = PaymentGatewayFactory.get_gateway(method)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Local Record (Pending)
        amount_paid = request.data.get('amount_paid', ride.estimated_fare)
        payment, _ = Payment.objects.update_or_create(
            ride=ride,
            defaults={
                'amount': amount_paid,
                'status': 'PENDING',
                'provider': getattr(gateway, 'provider_name', 'DEMO')
            }
        )

        # 3. Initiate with Provider
        init_data = gateway.initiate_payment(
            float(amount_paid), 
            ride.id, 
            request.user.email or f"{request.user.username}@example.com"
        )

        if init_data.get('status') == 'SUCCESS':
            # Update local record with provider's transaction ID if available
            if init_data.get('transaction_id'):
                payment.transaction_id = init_data['transaction_id']
                payment.save()
            
            # If it's CASH, we do NOT finish yet. We wait for Driver Confirmation.
            if method == 'CASH':
                # Notify Driver to Confirm
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[CASH PAYMENT] Broadcasting PAYMENT_PENDING for ride {ride.id} to channel ride_{ride.id}")
                print(f"[CASH PAYMENT DEBUG] Broadcasting to ride_{ride.id} - Amount: {amount_paid}")
                
                from channels.layers import get_channel_layer
                from asgiref.sync import async_to_sync
                layer = get_channel_layer()
                async_to_sync(layer.group_send)(
                    f"ride_{ride.id}",
                    {
                        "type": "ride_status_update",
                        # We use a special status or just 'PAID' but with a flag? 
                        # Let's use 'PAYMENT_PENDING' as agreed or just 'PAID' status on Ride 
                        # but keeping Payment as PENDING.
                        # Actually, keeping Ride as COMPLETED or similar until confirmed is safer.
                        # But UI needs to know. Let's send a custom 'cash_pending_confirmation' event via status update.
                        "status": "PAYMENT_PENDING", # Frontend will handle this to show 'Waiting for Driver'
                        "ride_id": ride.id,
                        "amount_paid": float(amount_paid),
                        "driver_name": ride.driver.username if ride.driver else "Driver"
                    }
                )
                
                logger.info(f"[CASH PAYMENT] Broadcast complete for ride {ride.id}")
                print(f"[CASH PAYMENT DEBUG] Broadcast sent successfully")
                
                return Response({
                    "status": "PENDING", 
                    "message": "Cash payment recorded. Waiting for driver confirmation.",
                    "is_cash": True
                }, status=status.HTTP_200_OK)
            
            return Response({"checkout_url": init_data.get('payment_url')}, status=status.HTTP_200_OK)
        
        return Response({"error": init_data.get('message', 'Initiation failed')}, 
                        status=status.HTTP_400_BAD_REQUEST)

class PaymentCallbackView(APIView):
    """
    Global callback handler for all payment providers.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # We handle GET for demo/simple redirects, POST for real webhooks
        return self.handle_callback(request.query_params)

    def post(self, request):
        return self.handle_callback(request.data)

    def handle_callback(self, data):
        gateway = PaymentGatewayFactory.get_gateway()
        verification = gateway.verify_payment(data)

        if verification.get('status') == 'SUCCESS':
            # Success logic
            trx_id = verification.get('transaction_id')
            payment = get_object_or_404(Payment, transaction_id=trx_id)
            
            # Use PaymentService to handle business logic (commissions, wallets, statuses)
            PaymentService.process_payment_success(payment.id)
            
            return Response({"status": "SUCCESS", "message": "Payment processed."}, status=status.HTTP_200_OK)
        
        return Response({"status": "FAILED", "message": verification.get('message')}, 
                        status=status.HTTP_400_BAD_REQUEST)

class DemoPaymentCallbackView(APIView):
    """
    Specific endpoint for the Demo (fake) flow to simulate a user 
    being redirected back from a gateway.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        ride_id = request.query_params.get('ride_id')
        trx_id = request.query_params.get('trxID')
        
        # In a real app, this would be a frontend success page
        # For this demo, let's just trigger the callback logic directly
        gateway = PaymentGatewayFactory.get_gateway()
        verification = gateway.verify_payment(request.query_params)
        
        if verification.get('status') == 'SUCCESS':
            payment = get_object_or_404(Payment, transaction_id=trx_id)
            PaymentService.process_payment_success(payment.id)
            return Response({
                "message": "DEMO PAYMENT SUCCESS!",
                "details": f"Ride #{ride_id} is now PAID. Driver wallet updated and commission deducted."
            })
        
        return Response({"error": "Payment failed"}, status=status.HTTP_400_BAD_REQUEST)

class WalletStatsView(APIView):
    """
    Get wallet balance and transaction stats for the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import Wallet, Transaction, Payment
        from django.db.models import Sum
        
        user = request.user
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        # Get transaction totals
        total_earnings = Transaction.objects.filter(
            wallet=wallet, 
            transaction_type='EARNING'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Total spent (for passengers)
        total_spent = Payment.objects.filter(
            ride__rider=user, 
            status='COMPLETED'
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        # Recent activities (last 20)
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-timestamp')[:20]
        
        transactions_data = [{
            'id': t.id,
            'type': t.transaction_type,
            'amount': float(t.amount),
            'description': t.description,
            'timestamp': t.timestamp.isoformat()
        } for t in transactions]
        
        return Response({
            'total_income': float(total_earnings),
            'wallet_balance': float(wallet.balance),
            'total_spent': float(total_spent),
            'recent_transactions': transactions_data
        })

class ConfirmCashPaymentView(APIView):
    """
    Allows Driver to confirm they received the CASH from the Passenger.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ride_id = request.data.get('ride_id')
        user = request.user
        
        # Verify ride exists and user is the driver
        ride = get_object_or_404(Ride, id=ride_id)
        
        # Check if user is the driver
        if ride.driver != user:
            return Response({"error": "Only the assigned driver can confirm payment."}, 
                            status=status.HTTP_403_FORBIDDEN)
                            
        # Find the PENDING cash payment
        payment = Payment.objects.filter(ride=ride, status='PENDING', provider='DEMO').first() 
        # Note: Provider might be 'CASH' or 'DEMO' depending on factory.
        # Let's check generally for pending payment
        if not payment:
            payment = Payment.objects.filter(ride=ride, status='PENDING').first()
            
        if not payment:
            return Response({"error": "No pending payment found for this ride."}, 
                            status=status.HTTP_404_NOT_FOUND)
                            
        # Process the payment success
        # This updates Payment -> COMPLETED, Ride -> FINISHED, and adds Transaction
        PaymentService.process_payment_success(payment.id)
        
        # Broadcast FINISHED status to both driver and passenger
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            f"ride_{ride.id}",
            {
                "type": "ride_status_update",
                "status": "FINISHED",
                "ride_id": ride.id
            }
        )
        
        return Response({
            "status": "SUCCESS",
            "message": "Payment confirmed. Ride finished."
        })
