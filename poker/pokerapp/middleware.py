from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.db import close_old_connections

@database_sync_to_async
def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()

        # Get the token from query string or headers
        query_string = parse_qs(scope["query_string"].decode())
        token_key = query_string.get("token")

        if not token_key:
            headers = dict(scope["headers"])
            # Check for Authorization header (with Bearer token)
            auth_header = headers.get(b'authorization', None)
            if auth_header:
                auth_header = auth_header.decode('utf-8')
                if auth_header.startswith('Bearer '):
                    token_key = auth_header.split(' ')[1]

        # Authenticate the user
        if token_key:
            print("found token_key")
            scope["user"] = await get_user_from_token(token_key)

        return await super().__call__(scope, receive, send)