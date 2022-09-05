# Foodgram - Продуктовый помощник #

***

## Адрес сайта: http://158.160.6.245/

![workflow](https://github.com/Marsonic-del/yamdb_final/actions/workflows/main.yml/badge.svg)

## Описание: ##
***

Foodgram это ресурс для публикации рецептов. Пользователи могут создавать свои рецепты, читать рецепты других пользователей, подписываться на интересных авторов, добавлять лучшие рецепты в избранное, а также создавать список покупок и загружать его в pdf формате.

## Технологии
***

* [Python](https://www.python.org/)
* [Django](https://www.djangoproject.com/)
* [DjangoRestFramework](https://www.django-rest-framework.org/)
* [PostgresSQL](https://www.postgresql.org/)
* [Nginx](https://www.nginx.com/)
* [React](https://reactjs.org/)
* [Djoser](https://djoser.readthedocs.io/en/latest/)
* [Docker](https://www.docker.com/)

## Запуск проекта

Скачайте проект с репозитория на локальную машину:

    https://github.com/Marsonic-del/foodgram-project-react

```sh
cd infra
```

Создайте файл  .env в папке infra c константами:
  DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
  DB_NAME # имя базы данных
  POSTGRES_USER # логин для подключения к базе данных
  POSTGRES_PASSWORD # пароль для подключения к БД
  DB_HOST # название сервиса (контейнера)
  DB_PORT # порт для подключения к БД
  SECRET_KEY # секретный ключ с файла settings

Дальше:

```sh
docker-compose up -d
```

Миграции:
```sh
docker-compose exec backend python manage.py migrate
```

Создание суперюзера:

```sh
docker-compose exec web python manage.py createsuperuser
```

Собираем статику:
```sh
docker-compose exec web python manage.py collectstatic --no-input
```

Если нужно перенести локальную базу данных (файл dump.json):

```sh
docker cp fixtures.json <container_id>:/app
docker exec -it <container_id> bash
python3 manage.py shell
>>> from django.contrib.contenttypes.models import ContentType
>>> ContentType.objects.all().delete()
>>> quit()
python manage.py loaddata dump.json

```

Документация API доступна по адресу:
***
[http://localhost:8000/api/redoc/](http://localhost:8000/api/redoc/)

