import uuid, random
from rest_framework.permissions import BasePermission
from rest_framework.pagination import LimitOffsetPagination
import requests, typing, json
# from accounts.models import Dealer
from typing import Any, List


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


class IsDealerOrStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type in ['dealer', 'staff',] or request.user.is_admin:
            return True
            # dealer = Dealer.objects.get(request.kwargs)
            # if request.user.user_profile:
            #     return True
        return False
        
    def has_object_permission(self, request, view):
        if request.user.user_type in ['agent', 'staff', 'admin']:
            return True
        else:
            return False


class IsMechanicOnly(BasePermission):
    def has_permission(self, request, view):
        try:
            if request.user.user_type == 'mechanic':
                return True
            return False
        except:
            pass
        
    def has_object_permission(self, request, view):
        if request.user.user_type == 'mechanic':
            return True
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
    rand = f'{random.randrange(100, 999)}{random.randrange(111, 999)}'
    print(rand)
    return rand




 