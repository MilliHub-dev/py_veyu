import os, uuid, random
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import BasePermission
from rest_framework.pagination import LimitOffsetPagination
import requests, typing, json
from django.conf import settings
from typing import Any, List
from concurrent.futures import ThreadPoolExecutor


import uuid
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings

def upload_multiple_files(*files) -> list:
    """
    Handles multiple file uploads concurrently and returns a list of uploaded file details.
    
    Args:
        files (tuple): List of files from request.FILES.getlist('files').

    Returns:
        list: A list of dictionaries containing 'file', 'uuid' and 'url' for each uploaded file.
    """
    uploaded_files = []

    with ThreadPoolExecutor() as executor:
        uploaded_files = list(executor.map(upload_file, *files))
    return uploaded_files


def upload_file(file, upload_to=None):
    ext = os.path.splitext(file.name)[-1]
    upload_dir = os.path.join(
        settings.BASE_DIR,
        settings.MEDIA_DIR,
    )

    def save_file(file):
        if ext in ['.png', '.jpg', '.jpeg']:
            # create an image in e.g 
            # 'uploads/profiles' or 'uploads/vehicles'
            if upload_to:
                upload_dir = os.path.join(upload_dir, upload_to)
            upload_dir = os.path.join(upload_dir, 'vehicle/images/')
        elif ext in ['.pdf', '.txt', '.docx', '.csv', '.xlsx']:
            # create a file in 'uploads/docs'
            if upload_to:
                upload_dir = os.path.join(upload_dir, upload_to)
            upload_dir = os.path.join(upload_dir, 'docs/')
        
        file_path = os.path.join(upload_dir, f"{file_uuid}{ext}")
        file_obj = default_storage.save(file_path, ContentFile(file.read()))

        # Return file data
        return file_path



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




 