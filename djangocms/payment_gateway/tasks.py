from celery import shared_task
from .models import Payment, PaymentLog
import logging

logger = logging.getLogger(__name__)

@shared_task
def process_webhook(payment_id, event_data):
    """Process webhook asynchronously"""
    try:
        payment = Payment.objects.get(id=payment_id)
        payment.webhook_received = True
        payment.save()
        
        PaymentLog.objects.create(
            payment=payment,
            event_type='WEBHOOK_RECEIVED',
            message='Webhook processed successfully',
            data=event_data
        )
        
        # Add additional processing logic here
        # e.g., send confirmation emails, update inventory, etc.
        
        return f"Webhook processed for payment {payment_id}"
    
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
        return f"Payment {payment_id} not found"
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        return f"Webhook processing failed: {str(e)}"

@shared_task
def cleanup_old_payments():
    """Clean up old incomplete payments"""
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=7)
    old_payments = Payment.objects.filter(
        status='waiting',
        created__lt=cutoff_date
    )
    
    count = old_payments.count()
    old_payments.update(status='error')
    
    return f"Cleaned up {count} old payments"