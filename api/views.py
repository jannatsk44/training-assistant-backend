from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from rest_framework import viewsets, status
from rest_framework.decorators import action
from .models import *
import logging
from .langchain_service import *
import requests
from django.utils import timezone
from datetime import timedelta
from openai import OpenAI
from datetime import date
from django.conf import settings
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
import csv
from io import TextIOWrapper
from rest_framework.parsers import MultiPartParser, FormParser
import chardet  # library to detect encoding
from django.utils.encoding import smart_str
from django.core.mail import get_connection


# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Topic
from .serializers import TopicSerializer

class TopicListView(APIView):
    def get(self, request, *args, **kwargs):
        # Retrieve all Topic objects
        topics = Topic.objects.all()
        
        # Serialize them (id and name will automatically be included)
        serializer = TopicSerializer(topics, many=True)
        
        # Return the serialized data as a JSON response
        return Response(serializer.data, status=status.HTTP_200_OK)



class ProfilePicUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:
            # Get the logged-in user's profile
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            return Response({"error": "User profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProfilePicSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile picture updated successfully!", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import csv
from io import TextIOWrapper
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.utils.encoding import smart_str
import chardet
from .models import Topic, Question  # Adjust the import based on your project structure

class CSVUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('file')

        if not csv_file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File is not CSV type'}, status=status.HTTP_400_BAD_REQUEST)

        if csv_file.multiple_chunks():
            return Response({'error': f'Uploaded file is too big ({csv_file.size / (1024 * 1024):.2f} MB).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Detect file encoding
            file_head = csv_file.read(100)  # Read first 100 bytes to guess encoding
            detected_encoding = chardet.detect(file_head)
            encoding = detected_encoding['encoding'] if detected_encoding['encoding'] else 'utf-8'
            csv_file.seek(0)  # Reset file pointer to the start

            file_data = TextIOWrapper(csv_file.file, encoding=encoding, errors='replace')
            reader = csv.DictReader(file_data)

            for row in reader:
                topic_name = row.get('topic')
                if topic_name:
                    topic, _ = Topic.objects.get_or_create(name=topic_name)

                description = smart_str(row.get('description', ''), encoding='utf-8', errors='ignore')
                defaults = {key: smart_str(value, encoding='utf-8', errors='ignore') for key, value in row.items() if key not in ['description', 'topic']}

                Question.objects.update_or_create(
                    description=description,
                    defaults={**defaults, 'topic': topic}
                )

            return Response({'success': 'CSV file processed successfully'}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': f'Failed to process CSV file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


from django.core.mail import send_mail, get_connection
from django.utils.crypto import get_random_string
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from django.conf import settings
from .models import OTP

class GenerateOTPView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        email = request.data.get('email')

        # Validate the input email
        if not email:
            raise ValidationError({'email': 'This field is required.'})

        # Generate a random 6-digit OTP
        otp = get_random_string(length=6, allowed_chars='0123456789')

        # Check if OTP already exists for this email
        otp_entry, created = OTP.objects.update_or_create(email=email, defaults={'otp': otp})

        email_connection = get_connection(timeout=10)  # 10 seconds timeout

        # Send OTP via email
        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP code is {otp}. It is valid for 5 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
	    connection=email_connection, 
     

        )

        return Response({'message': 'OTP sent successfully.'}, status=status.HTTP_200_OK)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        if not email or not otp:
            raise ValidationError({'email': 'This field is required.', 'otp': 'This field is required.'})

        # Check if the OTP is valid
        otp_record = OTP.objects.filter(email=email, otp=otp).last()
        if otp_record and otp_record.is_valid():
            return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

class AdminOnlyView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, format=None):
        data = {"message": "Hello, admin!"}
        return Response(data)

class UserAndProfileAPIView(APIView):
    """
    Retrieve all users along with their profiles.
    """
    def get(self, request, format=None):
        users = User.objects.all()
        result = []

        for user in users:
            user_serializer = UserSerializer(user)
            try:
                user_profile = UserProfile.objects.get(user=user)
                profile_serializer = UserProfileSerializer(user_profile)
                profile_data = profile_serializer.data
            except UserProfile.DoesNotExist:
                # Provide default values for the missing profile
                profile_data = {
                    'openai_request_count': 0,
                    'token_consumption': 0,
                    'token_consumed_today': 0,
                    'no_of_easy_problems_solved': 0,
                    'no_of_medium_problems_solved': 0,
                    'no_of_hard_problems_solved': 0,
                    'total_problems_solved': 0,
                    'token_limit': 0
                }

            # Combine user data and profile data
            combined_data = {**user_serializer.data, **profile_data}
            result.append(combined_data)

        return Response(result)
   
class RegisterUserView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            email = request.data.get('email')
            if not email:
                raise ValidationError({'email': 'This field is required.'})


            # Send OTP via email
            send_mail(
                subject='Resitration Successful',
                message=f'You have been successfully registered',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({
                'username': user.username,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated access

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                user_profile, created = UserProfile.objects.get_or_create(user=user)
                user_profile.last_active = timezone.now()  # Update last active time
                user_profile.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'is_admin': user.is_superuser
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# View to handle questions and user-specific status updates
# views.py



class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().select_related('topic')
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def user_status(self, request):
        user = request.user
        questions = Question.objects.all()
        statuses = UserQuestionStatus.objects.filter(user=user)
        status_dict = {status_obj.question.id: status_obj.status for status_obj in statuses}

        result = []
        for question in questions:
            result.append({
                'question': QuestionSerializer(question).data,
                'status': status_dict.get(question.id, 'unsolved'),
                
            })
        return Response(result)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        user = request.user
        question = self.get_object()
        status_value = request.data.get('status', 'unsolved')
        language_value = request.data.get('language', None)  # e.g., "python", "javascript", etc.

        # Validate the status
        if status_value not in ['unsolved', 'attempted', 'solved']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

        # Update or create the UserQuestionStatus, now including language
        user_status, created = UserQuestionStatus.objects.update_or_create(
            user=user,
            question=question,
            defaults={
                'status': status_value,
                'language': language_value
            }
        )

        # Check if we need to update the user's profile counters
        if status_value == 'solved':
            # To avoid double counting, you might want to check if the previous status was already solved.
            # (You can add that logic by retrieving the previous status if needed.)
            user_profile, _ = UserProfile.objects.get_or_create(user=user)
            difficulty = question.difficulty.lower()

            if difficulty == 'easy':
                user_profile.no_of_easy_problems_solved += 1
            elif difficulty == 'medium':
                user_profile.no_of_medium_problems_solved += 1
            elif difficulty == 'hard':
                user_profile.no_of_hard_problems_solved += 1

            user_profile.total_problems_solved += 1

            # Update language-specific counters (ensure these fields exist in your UserProfile model)
            if language_value:
                language_value = language_value.lower()
                if language_value == 'python':
                    user_profile.no_of_python_problems_solved += 1
                elif language_value == 'javascript':
                    user_profile.no_of_javascript_problems_solved += 1
                elif language_value == 'java':
                    user_profile.no_of_java_problems_solved += 1
                elif language_value == 'cpp':
                    user_profile.no_of_cpp_problems_solved += 1
                elif language_value == 'c':
                    user_profile.no_of_c_problems_solved += 1
                elif language_value == 'csharp':
                    user_profile.no_of_csharp_problems_solved += 1
                elif language_value == 'go':
                    user_profile.no_of_go_problems_solved += 1
                elif language_value == 'php':
                    user_profile.no_of_php_problems_solved += 1
                
                # Add other languages as needed

            user_profile.save()

        return Response({'status': user_status.status, 'language': user_status.language})


import os
import subprocess
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CodeExecutionSerializer

class RunCodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CodeExecutionSerializer(data=request.data)
        if serializer.is_valid():
            language = serializer.validated_data['language']
            code = serializer.validated_data['code']
            input_data = serializer.validated_data.get('input_data', '')

            # Ensure MinGW is in PATH for C++ and C on Windows
            if os.name == "nt":
                mingw_path = r"C:\MinGW\bin"  # Update if needed
                os.environ["PATH"] += os.pathsep + mingw_path

            if language == 'python':
                cmd = ["python", "-c", code]

            elif language == 'cpp':
                cpp_file = "temp.cpp"
                exe_file = "./temp"

                with open(cpp_file, "w") as f:
                    f.write(code)
                compile_cmd = ["g++", cpp_file, "-o", exe_file]
                try:
                    compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
                except FileNotFoundError:
                    return Response({"error": "g++ not found. Ensure MinGW is installed and added to PATH."}, status=status.HTTP_400_BAD_REQUEST)
                if compile_result.returncode != 0:
                    return Response({"error": "Compilation failed", "details": compile_result.stderr}, status=status.HTTP_400_BAD_REQUEST)
                cmd = [exe_file]

            elif language == 'c':
                # Save C code to a temporary file
                c_file = "temp.c"
                exe_file = "temp.exe" if os.name == "nt" else "./temp.out"
                with open(c_file, "w") as f:
                    f.write(code)
                # Compile with gcc for C language
                compile_cmd = ["gcc", c_file, "-o", exe_file]
                try:
                    compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, check=True)
                except FileNotFoundError:
                    return Response({"error": "gcc not found. Ensure GCC is installed and added to PATH."}, status=status.HTTP_400_BAD_REQUEST)
                if compile_result.returncode != 0:
                    return Response({"error": "Compilation failed", "details": compile_result.stderr}, status=status.HTTP_400_BAD_REQUEST)
                cmd = [exe_file]

            elif language == 'java':
                match = re.search(r'public\s+class\s+(\w+)', code)
                if not match:
                    return Response({"error": "No public class found in Java code"}, status=status.HTTP_400_BAD_REQUEST)
                class_name = match.group(1)
                filename = f"{class_name}.java"
                with open(filename, "w") as f:
                    f.write(code)
                compile_cmd = ["javac", filename]
                compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return Response({"error": "Compilation failed", "details": compile_result.stderr}, status=status.HTTP_400_BAD_REQUEST)
                cmd = ["java", class_name]

            elif language == 'javascript':
                # Write JavaScript code to a temporary file and run it using Node.js
                js_file = "temp.js"
                with open(js_file, "w") as f:
                    f.write(code)
                cmd = ["node", js_file]

            elif language == 'go':
                go_path = r"C:\Go\bin"  
                os.environ["PATH"] += os.pathsep + go_path  
                go_file = "temp.go"
                with open(go_file, "w") as f:
                    f.write(code)
                cmd = ["go", "run", "temp.go"]
                try:
                    result = subprocess.run(cmd, input=input_data, text=True, capture_output=True, timeout=5)
                    return Response({"output": result.stdout, "error": result.stderr})
                except subprocess.TimeoutExpired:
                    return Response({"error": "Execution timed out"}, status=status.HTTP_400_BAD_REQUEST)

            elif language == 'php':
                php_path = r"C:\Program Files\php-8.4.3"  # Update to your PHP installation path
                os.environ["PATH"] += os.pathsep + php_path  # Add PHP to system PATH
                php_file = "temp.php"
                with open(php_file, "w") as f:
                    f.write(code)
                cmd = ["php", php_file]

            elif language == 'csharp' or language == 'cs':
                proj_folder = "csharp_project"
                cs_file = f"{proj_folder}/Program.cs"
                os.makedirs(proj_folder, exist_ok=True)
                if not os.path.exists(f"{proj_folder}/csharp_project.csproj"):
                    subprocess.run(["dotnet", "new", "console", "--name", proj_folder], capture_output=True, text=True)
                with open(cs_file, "w") as f:
                    f.write(code)
                compile_cmd = ["dotnet", "build", proj_folder, "-c", "Release"]
                compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
                if compile_result.returncode != 0:
                    return Response({"error": "Compilation failed", "details": compile_result.stderr}, status=status.HTTP_400_BAD_REQUEST)
                exe_path = f"{proj_folder}/bin/Release/net7.0/csharp_project.dll"
                cmd = ["dotnet", exe_path]

            try:
                result = subprocess.run(cmd, input=input_data, text=True, capture_output=True, timeout=5)
                return Response({"output": result.stdout, "error": result.stderr})
            except subprocess.TimeoutExpired:
                return Response({"error": "Execution timed out"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ActiveUsersByDateRangeAPIView(APIView):
    permission_classes = [IsAuthenticated]  # or IsAdminUser if needed

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if not start_date or not end_date:
            return Response({'error': 'start_date and end_date are required.'}, status=400)

        logs = UserActivityLog.objects.filter(activity_date__range=[start_date, end_date])
        # Aggregate active time per user or simply get distinct users.
        user_ids = logs.values_list('user', flat=True).distinct()
        users = UserProfile.objects.filter(user__id__in=user_ids)

        # Optionally, aggregate active time for each user:
        user_data = []
        for profile in users:
            total_active_time = logs.filter(user=profile.user).aggregate(total=Sum('active_time'))['total'] or 0
            user_data.append({
                'username': profile.user.username,
                'total_active_time': total_active_time,
                # Include any other fields you need...
            })

        return Response({'active_users': user_data})


class UpdateActiveTimeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_profile = user.profile
        current_time = timezone.now()
        time_diff = (current_time - user_profile.last_active).total_seconds() / 60

        # Update profile fields
        user_profile.session_time += time_diff
        user_profile.active_time_today += time_diff
        user_profile.last_active = current_time
        user_profile.save()

        # Update or create today's activity log
        today = current_time.date()
        activity_log, created = UserActivityLog.objects.get_or_create(user=user, activity_date=today)
        activity_log.active_time += time_diff
        activity_log.save()

        return Response({
            'status': 'active time updated',
            'session_time': user_profile.session_time,
            'active_time_today': user_profile.active_time_today
        })


class ChatHistoryAPIView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user  # Get the user from the request object.
        recent_chats = ChatHistory.objects.filter(user=user).order_by('-timestamp')[:50]  # Retrieve the last 50 messages.
        serializer = ChatHistorySerializer(recent_chats, many=True)  # Serialize the data.
        return Response(serializer.data, status=status.HTTP_200_OK)  # Return the serialized data.

    def post(self, request, *args, **kwargs):
        serializer = ChatHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()            
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class ChatAPIView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        recent_chats = ChatHistory.objects.filter(user=user).order_by('-timestamp')[:1]  # last 10 messages
        context_messages = [[{"role": "user", "content": chat.message},{"role": "assistant", "content": chat.response}] for chat in recent_chats]
        print(context_messages)
        user_prompt = request.data.get('messages')
        system_prompt = request.data.get('messages')
        system_prompt = system_prompt[0]['content']
        user_prompt = user_prompt[1]['content']
        context_messages.append([{"role": "user", "content": user_prompt},{"role": "assistant", "content": system_prompt}])
        if not user_prompt:
            return Response({"error": "Prompt is required"}, status=status.HTTP_400_BAD_REQUEST)
        client = OpenAI(api_key = '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')
        # Ideally, fetch context from chat history or pass relevant session tokens
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=context_messages[0],
            temperature = 0.2,
        )
        response_content = response.choices[0].message.content
        recent_chats = ChatHistory.objects.filter(user=user).order_by('-timestamp')
        usage = response.usage
        today = date.today()
        
        if recent_chats.count() > 16:
                # Get ids of old messages to delete (keep only 10 most recent)
                old_message_ids = recent_chats[10:].values_list('id', flat=True)[:10]
                ChatHistory.objects.filter(id__in=old_message_ids).delete()
        # Store the new conversation in history
        ChatHistory.objects.create(
            user=request.user,
            message=user_prompt,
            response=response_content
        )
        user_profile = user.profile
        user_profile.openai_request_count += 1
        if user_profile.last_token_consumption_date != today:
            user_profile.token_consumed_today = 0
            user_profile.last_token_consumption_date = today
        if usage:
            user_profile.token_consumption += usage.total_tokens
            user_profile.token_consumed_today += usage.total_tokens
        user_profile.save()

        return Response({"response": response_content}, status=status.HTTP_200_OK)

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        try:
            profile = user.profile
            profile_data = {
                'profile_pic': request.build_absolute_uri(profile.profile_pic.url) if profile.profile_pic else None,
                'openai_request_count': profile.openai_request_count,
                'token_consumption': profile.token_consumption,
                'token_consumed_today': profile.token_consumed_today,
                'active_time_today': profile.active_time_today,
                'no_of_easy_problems_solved' :profile.no_of_easy_problems_solved,
                'no_of_medium_problems_solved': profile.no_of_medium_problems_solved,
                'no_of_hard_problems_solved': profile.no_of_hard_problems_solved,
                'total_problems_solved': profile.total_problems_solved,
                'token_limit': profile.token_limit,
            }
        except UserProfile.DoesNotExist:
            profile_data = {}

        response_data = {**user_data, **profile_data}  # Merge user and profile data
        return Response(response_data)


class DashboardStatsAPIView(APIView):
    permission_classes = [IsAdminUser]  # Ensure only admins can access

    def get(self, request, format=None):
        total_users = User.objects.count()
        active_threshold = timezone.now() - timedelta(minutes=15)
        active_users = UserProfile.objects.filter(last_active__gte=active_threshold).count()

        # Now safely query the session_time
        total_time = UserProfile.objects.aggregate(total=Sum('session_time'))['total'] or 0

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'total_time_spent': total_time,
        })

class UpdateActiveTimeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_profile = user.profile

        # If last_active is not set, initialize it.
        if not user_profile.last_active:
            user_profile.last_active = timezone.now()
            user_profile.save()

        current_time = timezone.now()
        # Calculate time difference in minutes
        time_diff = (current_time - user_profile.last_active).total_seconds() / 60.0

        # Ensure we don't update with a negative time (if clocks are off, etc.)
        if time_diff < 0:
            time_diff = 0

        # Update the user's profile
        user_profile.session_time += time_diff
        user_profile.active_time_today += time_diff
        # Update the last active time to the current time
        user_profile.last_active = current_time
        user_profile.save()

        # Update or create today's activity log record
        today = current_time.date()
        activity_log, created = UserActivityLog.objects.get_or_create(
            user=user,
            activity_date=today
        )
        activity_log.active_time += time_diff
        activity_log.save()

        return Response({
            'status': 'active time updated',
            'session_time': user_profile.session_time,
            'active_time_today': user_profile.active_time_today,
            'log_active_time': activity_log.active_time,
        })


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        email = request.data['email']
        otp = get_random_string(length=6, allowed_chars='1234567890')
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        OTP.objects.filter(email=email).delete()

        # Create a new OTP entry
        OTP.objects.create(email=email, otp=otp)
        
        send_mail(
            subject='Reset Password',
            message=f'Your OTP to reset password: {otp}. It is valid for 5 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return JsonResponse({'message': 'OTP sent to your email.'})

    def get(self, request):
        return JsonResponse({'error': 'Invalid request'}, status=400)
    

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        email = request.data['email']
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)
        otp = request.data['otp']
        new_password = request.data['new_password']
        
        otp_instance = OTP.objects.filter(email=email, otp=otp).first()
        if otp_instance and otp_instance.is_valid():
            user = get_object_or_404(User, email=email)
            user.set_password(new_password)
            user.save()
            otp_instance.delete()  # Invalidate the OTP after use
            return JsonResponse({'message': 'Password has been reset successfully.'})
        else:
            return JsonResponse({'error': 'Invalid or expired OTP.'}, status=400)

    def get(self, request):
        return JsonResponse({'error': 'Invalid request'}, status=400)


class IncreaseTokenLimitView(APIView):

 def patch(self, request, user_id, *args, **kwargs):
        try:
            user_profile = UserProfile.objects.get(user__id=user_id)  # Fetch the user profile based on user_id
        except UserProfile.DoesNotExist:
            return Response({'error': 'UserProfile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = TokenLimitSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# views.py

# views.py

from collections import defaultdict
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserQuestionStatus

class UserPerformanceView(viewsets.ViewSet):
    def list(self, request):
        user_profiles = UserProfile.objects.all()
        user_activity_logs = UserActivityLog.objects.all()
        user_question_statuses = UserQuestionStatus.objects.all()

        user_data = []

        for user in user_profiles:
            activity_log = user_activity_logs.filter(user=user.user).order_by('-activity_date')
            question_status = user_question_statuses.filter(user=user.user)

            user_data.append({
                "username": user.user.username,
                "firstname": user.user.first_name,
                "lastname": user.user.last_name,
                "active_time_today": user.active_time_today,
                "total_problems_solved": user.total_problems_solved,
                "activity_log": [
                    {"date": log.activity_date, "active_time": log.active_time} for log in activity_log
                ],
                "question_status": [
                    {
                        "question": qs.question.name,
                        "difficulty": qs.question.difficulty,  # Include question difficulty
                        "status": qs.status,
                        "language": qs.language
                    }
                    for qs in question_status
                ]
            })

        return Response(user_data)

from collections import defaultdict
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import UserQuestionStatus  # Adjust if the path is different

class AdminUserPerformanceAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        # Fetch all solved statuses and include user and question
        solved_statuses = UserQuestionStatus.objects.filter(
            status='solved'
        ).select_related('user', 'question')

        user_performance = {}
        # Keep track of which questions have been counted per user
        counted_questions = defaultdict(set)

        for record in solved_statuses:
            user = record.user
            question_id = record.question.id

            # Skip if this question has already been counted for this user
            if question_id in counted_questions[user.id]:
                continue

            counted_questions[user.id].add(question_id)

            # Initialize user entry
            if user.id not in user_performance:
                user_performance[user.id] = {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "total_problems_solved": 0,
                    "languages": {}
                }

            lang = (record.language or "unknown").lower()
            difficulty = (record.question.difficulty or "unknown").lower()

            if lang not in user_performance[user.id]["languages"]:
                user_performance[user.id]["languages"][lang] = {
                    "easy": 0,
                    "medium": 0,
                    "hard": 0,
                    "total": 0
                }

            user_performance[user.id]["languages"][lang]["total"] += 1
            user_performance[user.id]["total_problems_solved"] += 1

            if difficulty in ["easy", "medium", "hard"]:
                user_performance[user.id]["languages"][lang][difficulty] += 1

        return Response({
            "user_performance": list(user_performance.values())
        })


class UniqueCompaniesAPIView(APIView):
    def get(self, request):
        # Fetch all companies from the Question model
        questions = Question.objects.all()
        all_companies = set()
        for question in questions:
            if question.companies:
                companies = question.companies.split("  \n")  # Split by double spaces and newline
                all_companies.update(companies)

        # Return the unique companies sorted alphabetically
        return Response(sorted(all_companies))
