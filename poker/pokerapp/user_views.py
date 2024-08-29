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
# from . import responses

@api_view(['POST'])
def register(request):
    """
    Sign up for an account

    Use api-token-auth endpoint get token
    """
    create_user_serializer = CreateUserSerializer(data=request.data, context={'request': request})
    create_user_serializer.is_valid(raise_exception=True)
    user = create_user_serializer.save()
    user_serializer = UserSerializer(user)
    # groups_helper.join_podtalk_general_group(user)
    return Response(user_serializer.data, status=status.HTTP_201_CREATED)

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
