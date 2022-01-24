#!/usr/bin/env sh

python ./manage.py migrate
python ./manage.py collectstatic --noinput
gunicorn --forwarded-allow-ips=* --bind 0.0.0.0:8000 -w 2 pollsapi.wsgi:application
