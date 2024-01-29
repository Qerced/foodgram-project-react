# Продуктовый помощник
Ссылка на проект в облаке: http://yapvm.ddns.net (сервис в данный момент закрыт)

![example workflow](https://github.com/qerced/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

## Описание
Продуктовый помощник - это проект, в котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис "Список покупок" позволяет пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологический стек
* Django
* Django REST framework
* Nginx
* Docker
* Postgres

## Локальный запуск

Перед запуском перейдите в директорию `infra` и создайте в ней `.env` файл. Для его заполнения руководствутейсь шаблоном ниже:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

Проект состоит из компонентов, которые объединяются в работающее приложение при помощи контейнеров Docker. Перед тем как приступить к запуску, [ознакомьтесь](https://www.docker.com/get-started/) с его установкой и настройкой на вашем компьютере.

Для того чтобы быстро развернуть сервис и его инфраструктуру, перейдите в директорию `infra` и используйте команду запуска контейнеров в фоновом режиме:

```
cd infra
docker-compose up -d
```

При выполнении, начнется загрузка необходимых для работы образов, из которых после будут созданы и запущены следующие контейнеры:
* db - сервер Postgres
* web - сам Django проект, который создаст и применит необходимые миграции и запустит свой HTTP-сервер
* frontend - подгототавливает файлы, необходимые для работы фронтенд-приложения
* nginx - сервер Nginx 1.19.3

Подробнее ознакомиться с настройкой каждого контейнера вы можете в [docker-compose.yml](https://github.com/Qerced/foodgram-project-react/blob/master/infra/docker-compose.yml).

## После запуска

В проекте подготовлены тестовые данные, которые находятся в `data`, чтобы наполнить ими базу данных используйте managment команду:

```
docker-compose exec web python manage.py import_data_to_orm
```

## Continuous Integration и Continuous Deployment

В проекте настроена работа с GitHub Actions. Последовательность команд при выгрузке проекта в репозиторий описана в [foodgram_workflow.yml](https://github.com/Qerced/foodgram-project-react/blob/master/.github/workflows/foodgram_workflow.yml). Для работы с workflow вам потребуется переопределить переменные [Secrets](https://docs.github.com/ru/actions/security-guides/using-secrets-in-github-actions) в среде своего репозитория.

Шаблон наполнения схож с `.env` из пункта [локального запуска](https://github.com/Qerced/foodgram-project-react#%D0%BB%D0%BE%D0%BA%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D0%B7%D0%B0%D0%BF%D1%83%D1%81%D0%BA):

```
DOCKER_USERNAME= for build and push to your docker hub
DOCKER_PASSWORD= for build and push to your docker hub
HOST= adress your host
USER= username your host
SSH_KEY= host access key
PASSPHRASE= user access password
DB_ENGINE= django.db.backends.postgresql
DB_NAME= postgres
POSTGRES_USER= postgres
POSTGRES_PASSWORD= postgres
DB_HOST= db
DB_PORT= 5432
TELEGRAM_TO= for notification after completion of workflow
TELEGRAM_TOKEN= for notification after completion of workflow
```

## API

Узнать больше о методах, реализованных в проекте, можно на странице документации [ReDoc](http://127.0.0.1/api/docs/).
Если вы еще не успели развернуть у себя проект, загрузите файл [openapi-schema.yml](https://github.com/Qerced/foodgram-project-react/blob/master/docs/openapi-schema.yml) на сайт [Swagger editor](https://editor.swagger.io/).

## Авторы:
- [Vakauskas Vitas](https://github.com/Qerced)
