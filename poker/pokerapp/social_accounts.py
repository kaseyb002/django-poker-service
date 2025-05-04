from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Error
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import Account
from . import table_member_write_helpers
import jwt

class GoogleIDTokenOnlyAdapter(GoogleOAuth2Adapter):
    def complete_login(self, request, app, token, **kwargs):
        # Instead of calling Google, decode the token locally
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
    

@receiver(user_signed_up)
def on_social_user_signed_up(request, user, **kwargs):
    # Only happens the first time this user signs in via Google/Apple

    # Create their Account record
    Account.objects.create(user=user)

    # Optional: auto-join poker table, set defaults, etc
    table_member_write_helpers.join_table_on_sign_up(user)


class AppleLoginView(SocialLoginView):
    adapter_class = AppleOAuth2Adapter