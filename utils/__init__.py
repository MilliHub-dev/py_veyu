import uuid, random
from rest_framework.permissions import BasePermission
from rest_framework.pagination import LimitOffsetPagination



class IsAgentOrStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type in ['agent', 'staff', 'admin']:
            return True
        else:
            return False
        
    def has_object_permission(self, request, view):
        if request.user.user_type in ['agent', 'staff', 'admin']:
            return True
        else:
            return False


class OffsetPaginator(LimitOffsetPagination):
    limit_query_param = 'per_page'
    offset_query_param = 'offset'

    def __init__(self, default_limit=25) -> None:
        self.default_limit = default_limit
        super().__init__()


class FieldMissingException(Exception):
    message = "field is required"

    

def make_UUID():
    return uuid.uuid1()

def make_random_otp():
    rand = f'{random.randrange(100, 999)}-{random.randrange(111, 999)}'
    print(rand)
    return rand





