#!/usr/bin/env sh

python ./manage.py migrate
python ./manage.py collectstatic --noinput
gunicorn --forwarded-allow-ips=* --bind 0.0.0.0:8080 -w 2 app.wsgi:application
