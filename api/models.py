from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.utils import timezone
from django.utils.crypto import get_random_string
import base64
from datetime import timedelta 

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_date = models.DateField(default=timezone.now)
    active_time = models.PositiveIntegerField(default=0)  # in minutes

    class Meta:
        unique_together = ('user', 'activity_date')

from django.db import models
from django.utils.timezone import now
from datetime import timedelta

class OTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return now() <= self.created_at + timedelta(minutes=5)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    openai_request_count = models.PositiveIntegerField(default=0)
    token_consumption = models.PositiveIntegerField(default=0)
    token_consumed_today = models.PositiveIntegerField(default=0)
    last_token_consumption_date = models.DateField(auto_now=True)
    token_limit = models.PositiveIntegerField(default=20000)
    no_of_easy_problems_solved = models.PositiveIntegerField(default=0)
    no_of_medium_problems_solved = models.PositiveIntegerField(default=0)
    no_of_hard_problems_solved = models.PositiveIntegerField(default=0)
    total_problems_solved = models.PositiveIntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    session_time = models.IntegerField(default=0)
    active_time_today = models.IntegerField(default=0)  # Active time in minutes for today
    last_reset = models.DateField(auto_now_add=True) 
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    no_of_javascript_problems_solved = models.PositiveIntegerField(default=0)
    no_of_python_problems_solved = models.PositiveIntegerField(default=0)
    no_of_cpp_problems_solved = models.PositiveIntegerField(default=0)
    no_of_java_problems_solved = models.PositiveIntegerField(default=0)
    no_of_c_problems_solved = models.PositiveIntegerField(default=0)
    no_of_csharp_problems_solved = models.PositiveIntegerField(default=0)
    no_of_go_problems_solved = models.PositiveIntegerField(default=0)
    no_of_php_problems_solved = models.PositiveIntegerField(default=0)

    degree = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    education_ssc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    education_hsc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graduation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passing_year = models.IntegerField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    courses_passed = models.TextField(blank=True, null=True)
    otp_key = models.CharField(max_length=10, blank=True, editable=False)  # adjust length as necessary

    def save(self, *args, **kwargs):
        if not self.otp_key:
            # Generate a random base32 encoded key when creating a new profile
            self.otp_key = base64.b32encode(get_random_string(length=20).encode()).decode('utf-8')
        super().save(*args, **kwargs)
    def update_session_time(self, minutes):
        """Utility method to update session time safely."""
        self.session_time += minutes
        self.save()
     
     
    def update_active_time(self, minutes):
        """Updates the active time for today and resets if a new day."""
        if self.last_reset < now().date():
            self.active_time_today = 0
            self.last_reset = now().date()
        self.active_time_today += minutes
        self.save()    

       
    def reset_daily_usage(self):
        """ Resets daily token usage if the day has changed. """
        if self.last_token_consumption_date < timezone.now().date():
            self.token_consumed_today = 0
            self.last_token_consumption_date = timezone.now().date()
            self.save()

    def __str__(self):
        return f"{self.user.username}"


class Topic(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name
    
# Question model
class Question(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('complex', 'Complex'),
    ]
    
    STATUS_CHOICES = [
        ('unsolved', 'Unsolved'),
        ('attempted', 'Attempted'),
        ('solved', 'Solved'),
    ]
    
    name = models.CharField(max_length=1255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    answer = models.TextField()
    companies = models.TextField(null=True)
    
    def __str__(self):
        return self.name

# UserQuestionStatus model to track user-specific question status
class UserQuestionStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Question.STATUS_CHOICES, default='unsolved')
    language = models.CharField(max_length=50, blank=True, null=True)  # Store the language directly

    class Meta:
        unique_together = ('user', 'question')  # Ensure each user-question pair is unique

    def __str__(self):
        return f"{self.user.username} - {self.question.name} - {self.status} - {self.language}"

class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    message = models.TextField()  
    response = models.TextField()  
    timestamp = models.DateTimeField(auto_now_add=True)  
    
    def __str__(self):
        return f"Chat history for {self.user.username} on {self.timestamp}"