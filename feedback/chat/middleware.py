from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from accounts.models import Account


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

    def has_auth_header(self, scope):
        authorization_header = None

        # Loop through the headers and find the 'authorization' header
        for header in scope["headers"]:
            name, value = header
            if name == b'authorization':  # Headers are in bytes, so check with byte strings
                authorization_header = value.decode('utf-8')  # Decode the value to string

        # If the authorization header exists, split it to get the token
        if authorization_header:
            token = authorization_header.split('Token ')[1]  # Use index 1 for the token part
            return (True, token)
        else:
            token = None  # Handle missing authorization
            return (False, token)

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).
        has_auth_header, token = self.has_auth_header(scope)
        if has_auth_header:
            scope['user'] = await get_user(token)
            print("User:", scope['user'])
        return await self.app(scope, receive, send)