from rest_framework import viewsets, status
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer
from .utils.chapa import initiate_payment, verify_payment
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .tasks import send_booking_email  



class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def perform_create(self, serializer):
        booking = serializer.save()
        # Trigger email asynchronously with Celery
        send_booking_email.delay(booking.id, booking.user.email)






class InitiatePaymentView(APIView):
    def post(self, request):
        booking_ref = request.data.get("booking_reference")
        amount = request.data.get("amount")
        email = request.data.get("email")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        # Create Payment record
        payment = Payment.objects.create(
            booking_reference=booking_ref,
            amount=amount,
        )

        chapa_response = initiate_payment(booking_ref, amount, email, first_name, last_name)

        if chapa_response.get("status") == "success":
            checkout_url = chapa_response["data"]["checkout_url"]
            transaction_id = chapa_response["data"]["tx_ref"]
            payment.transaction_id = transaction_id
            payment.save()
            return Response({"checkout_url": checkout_url}, status=status.HTTP_200_OK)

        return Response(chapa_response, status=status.HTTP_400_BAD_REQUEST)


class VerifyPaymentView(APIView):
    def get(self, request, transaction_id):
        payment = get_object_or_404(Payment, transaction_id=transaction_id)
        chapa_response = verify_payment(transaction_id)

        if chapa_response.get("status") == "success":
            payment.status = "completed"
            payment.save()
            # TODO: trigger Celery email task
            return Response({"message": "Payment verified successfully"}, status=status.HTTP_200_OK)

        payment.status = "failed"
        payment.save()
        return Response({"message": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
