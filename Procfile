web: gunicorn app:flask_app
worker: celery -A tasks worker -E -B --loglevel=INFO
