from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.models import Account
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(token):
    try:
        return Account.objects.get(api_token=token)
    except Account.DoesNotExist:
        return AnonymousUser()


class ApiTokenAuthMiddleware:
    """
    Custom middleware gets user from Token.
    """

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    def extract_token(self, scope):
        """
        Extracts the API token from the query string.
        """
        query_string = scope["query_string"].decode()  # Convert bytes to string
        query_params = parse_qs(query_string)  # Parse query string

        token_list = query_params.get("token", [])  # Get token from query
        return token_list[0] if token_list else None  # Return token if exists

    async def __call__(self, scope, receive, send):
        token = self.extract_token(scope)

        if token:
            scope["user"] = await get_user(token)  # Authenticate user with token
        else:
            scope["user"] = AnonymousUser()  # Fallback to an anonymous user

        return await self.app(scope, receive, send)
