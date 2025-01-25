import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'motaa.settings')
django.setup()

# Example Django code
from chat.models import ChatRoom

print(ChatRoom.objects.all())
