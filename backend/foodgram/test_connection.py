import os
import time

import psycopg2


print('waiting database connection')
is_no_connection = True
while is_no_connection:
    connection = False
    try:
        psycopg2.connect(
            host='db',
            port='5432',
            password='postgres',
            user='postgres'
        )
        connection = True
    except psycopg2.OperationalError:
        print('no database connection, connection restarted')
        time.sleep(5)
    if connection:
        print('successful connection')
        os.system('python manage.py makemigrations user')
        os.system('python manage.py makemigrations recipes')
        os.system('python manage.py migrate')
        os.system('python manage.py collectstatic --noinput')
        os.system('gunicorn foodgram.wsgi:application --bind 0:8000')
        is_no_connection = False
