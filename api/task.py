# myapp/tasks.py
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import OTP
from django.conf import settings

def generate_and_send_otp(email):
    # Generate a random 6-digit OTP
    otp = get_random_string(length=6, allowed_chars='0123456789')

    # Save OTP to database
    OTP.objects.create(email=email, otp=otp)

    # Send OTP via email
    send_mail(
        subject='Your OTP Code',
        message=f'Your OTP code is {otp}. It is valid for 5 minutes.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
