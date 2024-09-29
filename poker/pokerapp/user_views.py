from django.shortcuts import render
from django.contrib.auth.models import User
from .models import *
from .serializers import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from . import responses

@api_view(['POST'])
def register(request):
    """
    Sign up for an account

    Use api-token-auth endpoint get token
    """
    create_user_serializer = CreateUserSerializer(data=request.data, context={'request': request})
    create_user_serializer.is_valid(raise_exception=True)
    user = create_user_serializer.save()
    # groups_helper.join_podtalk_general_group(user)
    user_serializer = UserSerializer(user, context={'request': request})
    token, created = Token.objects.get_or_create(user=user)
    return Response(
        {
            'token': token.key,
            'user': user_serializer.data,
        },
        status=status.HTTP_201_CREATED
    )

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def my_user(request):
    """
    Returns user's account
    """
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username:
            return responses.missing_parameter("username")
        if not password:
            return responses.missing_parameter("password")

        user = get_user(username)
        if not user:
            return responses.not_found("User does not exist for that email or username.")

        if not user.check_password(password):
            return responses.not_found("Wrong password.")

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
        })

def get_user(username):
    try:
        user = User.objects.get(username__iexact=username)
        return user
    except User.DoesNotExist:
        pass
    try:
        user = User.objects.get(email__iexact=username)
        return user
    except User.DoesNotExist:
        pass
    return None

@api_view(['GET'])
def username_is_valid(request):
    """
    Check if username is available.
    """
    class Serializer(serializers.Serializer):
        username = serializers.CharField(min_length=2, max_length=30)
    serializer = Serializer(data=request.query_params, context={'request': request})
    serializer.is_valid(raise_exception=True)
    username = serializer.data['username']
    is_unique = username_is_unique(username)
    if not is_unique:
        return Response(data={"detail": "USERNAME_TAKEN"})
    return Response(data={"detail": "VALID"})

def username_is_unique(username):
    try:
        user = User.objects.get(username__iexact=username)
        return False
    except User.DoesNotExist:
        return True

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def update_username(request):
    """
    Updates user's username
    """
    class UpdateUsernameSerializer(serializers.Serializer):
        username = serializers.CharField(min_length=2, max_length=30)
    serializer = UpdateUsernameSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    new_username = serializer.data['username']

    if User.objects.filter(username__iexact=new_username).exists():
        return responses.bad_request("USERNAME_TAKEN")

    request.user.username = new_username
    request.user.save()

    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def update_profile_image(request):
    """
    Updates user's profile image
    """
    class UpdateProfileImageSerializer(serializers.Serializer):
        image_url = serializers.URLField(max_length=250, min_length=None, allow_blank=False)
    serializer = UpdateProfileImageSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    new_profile_image = serializer.data['image_url']
    request.user.account.image_url = new_profile_image
    request.user.account.save()
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)
