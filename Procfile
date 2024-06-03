web: gunicorn app:flask_app
worker: celery -A tasks worker --loglevel=info
