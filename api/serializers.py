from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *
from rest_framework import serializers
from .models import Topic

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name']  # Include the fields you want to expose in the API

class ProfilePicSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['profile_pic']

# class UserPerformanceSerializer(serializers.ModelSerializer):
#     last_active_date = serializers.DateField(source='user.last_login')  # Adjust field name

#     class Meta:
#         model = UserPerformance
#         fields = ['username', 'total_problems_solved', 'languages', 'last_active_date']
        

        
class UserProfileSerializer2(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(use_url=True, required=False) 
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_pic',
            'degree',
            'phone',
            'city',
            'education_ssc',
            'education_hsc',
            'graduation',
            'passing_year',
            'date_of_joining',
            'courses_passed'
        ]

from django.db import transaction

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer2(required=True)

    class Meta:
        model = User
        fields = ['id','username', 'email', 'password', 'first_name', 'last_name', 'profile']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', {})
        with transaction.atomic():
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name']
            )
            UserProfile.objects.create(user=user, **profile_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    remaining_tokens = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = [
            'openai_request_count',
            'token_consumption',
            'token_consumed_today',
            'remaining_tokens',
            'no_of_easy_problems_solved',
            'no_of_medium_problems_solved',
            'no_of_hard_problems_solved',
            'total_problems_solved',
            'last_active',
            'active_time_today',
            'token_limit'
        ]

    def get_remaining_tokens(self, obj):
        obj.reset_daily_usage()  # Ensure the daily usage is reset if the day has changed
        return max(0, obj.token_limit - obj.token_consumption)

class TokenLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['token_limit']

    def validate_token_limit(self, value):
        # Check if the new token limit is greater than the current limit
        if value <= self.instance.token_limit:
            raise serializers.ValidationError("New token limit must be greater than the current limit.")
        return value
        
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        # Ensure that the username and password are correct
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid credentials')
        return data

# class TopicSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Topic
#         fields = ['name'] 

class QuestionSerializer(serializers.ModelSerializer):
    topic_name = serializers.CharField(source='topic.name', read_only=True)
    topic = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all())

    class Meta:
        model = Question
        fields = ['id', 'name', 'topic', 'topic_name', 'description', 'difficulty', 'answer', 'companies']



    def get_topic(self, obj):
        # Return the name of the topic directly
        return obj.topic.name if obj.topic else None

class UserQuestionStatusSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = UserQuestionStatus
        fields = ['question', 'status','language']


class ChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ['message', 'response', 'timestamp'] 
        
from rest_framework import serializers

class CodeExecutionSerializer(serializers.Serializer):
    language = serializers.ChoiceField(choices=['python', 'cpp', 'java', 'javascript', 'csharp', 'php', 'go', 'c'])
    code = serializers.CharField(required=False, default="")  # Now optional with a default empty string.
    input_data = serializers.CharField(required=False, allow_blank=True)