from django.shortcuts import render


def email_view(request, email=None):
    template = 'welcome.html'
    if email:
        template = f'{email}.html'
    return render(request, template, {'user': request.user})



