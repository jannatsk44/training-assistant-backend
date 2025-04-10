from django.utils import timezone
from .models import UserProfile
from django.utils.timezone import now


class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated:
            # Update last active time; ensure it doesn't drastically affect performance
            UserProfile.objects.filter(user=request.user).update(last_active=timezone.now())

        return response

from django.utils import timezone
from datetime import timedelta

class SessionTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            current_time = timezone.now()
            try:
                profile = UserProfile.objects.get(user=request.user)
                if hasattr(profile, 'last_session_update'):
                    time_diff = current_time - profile.last_session_update
                    minutes_diff = time_diff.total_seconds() / 60
                    profile.update_session_time(int(minutes_diff))
                profile.last_session_update = current_time
                profile.save()
            except UserProfile.DoesNotExist:
                pass
        return response

class UpdateActiveTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                if profile.last_active:
                    time_diff = now() - profile.last_active
                    minutes_diff = time_diff.total_seconds() / 60
                    profile.update_active_time(int(minutes_diff))
            except UserProfile.DoesNotExist:
                pass
        return response
