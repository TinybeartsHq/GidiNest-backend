web: gunicorn gidinest_backend.wsgi --log-file -
worker: celery -A gidinest_backend worker -l info
