from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings



@shared_task
def send_notification():
    print("Sending Notification...")
    return "Done"



@shared_task
def send_payment_confirmation_email(email, booking_reference):
    send_mail(
        "Payment Successful",
        f"Your payment for booking {booking_reference} was successful.",
        "noreply@yourapp.com",
        [email],
    )




@shared_task
def send_booking_email(booking_id, user_email):
    """
    Task to send booking confirmation email
    """
    subject = "Booking Confirmation"
    message = f"Your booking with ID {booking_id} has been successfully created."
    from_email = settings.DEFAULT_FROM_EMAIL  # make sure this is set in settings.py

    send_mail(subject, message, from_email, [user_email])
