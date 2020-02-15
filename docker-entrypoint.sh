#!/bin/sh

# Apply database migrations
python manage.py migrate
# Collect static files
python manage.py collectstatic --noinput

# Prepare log files and start outputting logs to stdout
mkdir /srv/logs
touch /srv/logs/gunicorn.log
touch /srv/logs/access.log
tail -n 0 -f /srv/logs/*.log &

# Start Gunicorn processes
echo Starting Gunicorn...
exec gunicorn vw_type2_id.wsgi:application \
    --name vw_type2_id \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --log-file=/srv/logs/gunicorn.log \
    --access-logfile=/srv/logs/access.log \
    "$@"
