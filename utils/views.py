from django.shortcuts import render
from django.conf import settings

def index_view(request):
    template = settings.BASE_DIR / 'feedback/templates/chat.html'
    return render(request, template, {'user': request.user})

def chat_view(request, room_name):
    template = settings.BASE_DIR / 'feedback/templates/chat.html'
    return render(request, template, {'user': request.user, 'room_name': room_name})



