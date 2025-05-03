from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.socialaccount.models import SocialLogin
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import Account
from . import table_member_write_helpers
import jwt

# Google Adapter and Login
class GoogleIDTokenOnlyAdapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        try:
            data = jwt.decode(
                token.token,
                options={"verify_signature": False, "verify_aud": False}
            )
        except jwt.DecodeError:
            raise OAuth2Error("Could not decode ID token")

        login = self.get_provider().sociallogin_from_response(request, data)
        return login

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleIDTokenOnlyAdapter

# Apple Adapter and Login (customized to fill missing email)
class AppleIDTokenAdapter(AppleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs) -> SocialLogin:
        login = super().complete_login(request, app, token, **kwargs)
        user = login.user

        # Fallback email
        if not user.email:
            uid = login.account.uid
            user.email = f"{uid}@apple.appleid.local"

        # Fallback username
        if not user.username:
            provider = login.account.provider  # e.g., "apple"
            uid = login.account.uid[:8]  # short unique identifier
            user.username = f"{provider}_{uid}"

        return login

class AppleLoginView(SocialLoginView):
    adapter_class = AppleIDTokenAdapter

# Signal: On first-time signup via social login
@receiver(user_signed_up)
def on_social_user_signed_up(request, user, **kwargs):
    Account.objects.create(user=user)
    table_member_write_helpers.join_table_on_sign_up(user)