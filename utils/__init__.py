import os, uuid, random
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.permissions import BasePermission
from rest_framework.pagination import LimitOffsetPagination
import requests, typing, json
from django.conf import settings
from typing import Any, List
from concurrent.futures import ThreadPoolExecutor
from django.core.files import File  
from datetime import datetime

def convert_js_date_to_django(js_date: str) -> str:
    """Converts a JavaScript locale date (MM/DD/YYYY) to Django date format (YYYY-MM-DD)."""
    try:
        parsed_date = datetime.strptime(js_date, "%m/%d/%Y")
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Expected MM/DD/YYYY.")
        

def upload_multiple_files(files) -> list:
    """
    Handles multiple file uploads concurrently and returns a list of uploaded file details.
    
    Args:
        files (tuple): List of files from request.FILES.getlist('files').

    Returns:
        list: A list of dictionaries containing 'file', 'uuid' and 'url' for each uploaded file.
    """
    uploaded_files = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(upload_file, file) for file in files]
        for future in futures:
            result = future.result()
            if result:
                uploaded_files.append(result)
    return uploaded_files


def upload_file(file, upload_to=None):
    ext = os.path.splitext(file.name)[-1]
    upload_dir = settings.MEDIA_ROOT

    if ext in ['.png', '.jpg', '.jpeg']:
        if upload_to:
            upload_dir = os.path.join(upload_dir, upload_to)
        upload_dir = os.path.join(upload_dir, 'vehicle/images/')
    elif ext in ['.pdf', '.txt', '.docx', '.csv', '.xlsx']:
        if upload_to:
            upload_dir = os.path.join(upload_dir, upload_to)
        upload_dir = os.path.join(upload_dir, 'docs/')
    
    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_uuid}{ext}")

    # Save the file using Django's storage system
    file_obj = default_storage.save(file_path, ContentFile(file.read()))

    # Return a Django File object instead of a raw path
    return File(default_storage.open(file_obj), name=file_obj)


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




 