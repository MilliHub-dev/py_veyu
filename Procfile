web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn veyu.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py runworker
release: python manage.py migrate