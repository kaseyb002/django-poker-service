from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

class AppleLogin(SocialLoginView):
    adapter_class = AppleOAuth2Adapter