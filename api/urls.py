from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'user-performance', UserPerformanceView, basename='user-performance')

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),  # User registration
    path('login/', LoginUserView.as_view(), name='login'),  # User login
    path('run-code/', RunCodeAPIView.as_view(), name='run_code'),
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('chat/history/', ChatHistoryAPIView.as_view(), name='chat-history'),
    path('user-details/', UserAndProfileAPIView.as_view(), name='user-details'),
    path('current-user/', CurrentUserAPIView.as_view(), name='current-user'),
    path('dashboard/', DashboardStatsAPIView.as_view(), name='dashboard'),
    path('update-active-time/', UpdateActiveTimeView.as_view(), name='update-active-time'),
    path('generate-otp/', GenerateOTPView.as_view(), name='generate-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('increase-token-limit/<int:user_id>/', IncreaseTokenLimitView.as_view(), name='increase-token-limit'),
    path('upload-questions-csv/', CSVUploadView.as_view(), name='upload-questions-csv'),
    path('update-pic/', ProfilePicUpdateView.as_view(), name='profile-pic-update'),
    path('topics/', TopicListView.as_view(), name='topic-list'),
    

    path('', include(router.urls)),  # Include all viewsets from router
]
