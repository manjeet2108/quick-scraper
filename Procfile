web: python manage.py collectstatic --noinput && gunicorn sociax_sync.wsgi:application --bind 0.0.0.0:$PORT
sync: python manage.py run_sync
worker: python manage.py export_jobs
