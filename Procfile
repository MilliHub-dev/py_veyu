web: DJANGO_SETTINGS_MODULE=veyu.render_settings gunicorn veyu.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile - --log-level info
worker: DJANGO_SETTINGS_MODULE=veyu.render_settings python manage.py runworker
release: DJANGO_SETTINGS_MODULE=veyu.render_settings python manage.py migrate