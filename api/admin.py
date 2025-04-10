from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Question)
admin.site.register(UserQuestionStatus)
admin.site.register(ChatHistory)
admin.site.register(UserProfile)
admin.site.register(OTP)
admin.site.register(Topic)

admin.site.register(UserActivityLog)