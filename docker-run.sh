nginx
cron
python3 /December/December/manage.py makemigrations && \
    python3 /December/December/manage.py migrate
uwsgi --chdir /December/December --socket :8001 --module December.wsgi
