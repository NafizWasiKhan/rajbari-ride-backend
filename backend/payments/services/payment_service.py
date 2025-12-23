from decimal import Decimal
from django.db import transaction as db_transaction
from ..models import Payment, Wallet, Transaction
from rides.models import Ride

class PaymentService:
    """
    Core service to handle payment-related business logic,
    including platform commission and driver wallet updates.
    """

    COMMISSION_RATE = Decimal('0.00')  # Disabled for now

    @staticmethod
    def process_payment_success(payment_id: int):
        """
        Handles post-payment success logic:
        1. Update Payment status to COMPLETED.
        2. Calculate platform commission.
        3. Credit remaining amount to driver wallet.
        4. Create system/driver transactions.
        5. Mark Ride as PAID.
        """
        with db_transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment_id)
            if payment.status == 'COMPLETED':
                return

            ride = payment.ride
            driver = ride.driver
            
            # 1. Update Payment Status
            payment.status = 'COMPLETED'
            payment.save()

            # 2. Commission Calculation
            total_fare = payment.amount
            commission_amount = total_fare * PaymentService.COMMISSION_RATE
            driver_earning = total_fare - commission_amount

            # 3. Update Driver Wallet
            if driver:
                wallet, _ = Wallet.objects.get_or_create(user=driver)
                
                if payment.provider == 'CASH':
                    # For CASH, the driver already has the money physically.
                    # We do NOT add to wallet.balance.
                    # But we DO create EARNING transaction for statistics/reporting.
                    
                    # Create EARNING transaction for total income tracking
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=driver_earning,
                        transaction_type='EARNING',
                        ride=ride,
                        payment=payment,
                        description=f"Cash earning from Ride #{ride.id}"
                    )
                    
                    wallet.save()

                    if PaymentService.COMMISSION_RATE > 0:
                        # Only if commission is enabled, we verify/deduct from wallet
                        commission_amount = payment.amount * PaymentService.COMMISSION_RATE
                        wallet.balance -= commission_amount
                        wallet.save()

                        # Transaction for System Commission (Deducted from driver)
                        Transaction.objects.create(
                            wallet=wallet,
                            amount=-commission_amount, 
                            transaction_type='COMMISSION',
                            ride=ride,
                            payment=payment,
                            description=f"Commission deduction for cash Ride #{ride.id}"
                        )
                else:
                    # For Digital (DEMO, BKASH, etc), we credit the driver's wallet
                    wallet.balance += driver_earning
                    wallet.save()

                    # Transaction for System Commission (Record)
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=commission_amount,
                        transaction_type='COMMISSION',
                        ride=ride,
                        payment=payment,
                        description=f"Platform fee for Ride #{ride.id} (Digital)"
                    )

                    # Driver Earning Record
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=driver_earning,
                        transaction_type='EARNING',
                        ride=ride,
                        payment=payment,
                        description=f"Earning from Ride #{ride.id}"
                    )

            # 4. Update Rider Transaction History
            if ride.rider:
                rider_wallet, _ = Wallet.objects.get_or_create(user=ride.rider)
                Transaction.objects.create(
                    wallet=rider_wallet,
                    amount=-total_fare, # Negative because it's a payment
                    transaction_type='RIDE_PAYMENT',
                    ride=ride,
                    payment=payment,
                    description=f"Payment for Ride #{ride.id} ({payment.provider})"
                )

            # 5. Mark Ride as FINISHED (payment completed and confirmed)
            ride.status = 'FINISHED'
            ride.save()

    @staticmethod
    def process_payment_failure(payment_id: int, reason: str = ""):
        """
        Handles payment failure logic.
        """
        payment = Payment.objects.get(id=payment_id)
        payment.status = 'FAILED'
        payment.save()
        # Log failure reason if needed
