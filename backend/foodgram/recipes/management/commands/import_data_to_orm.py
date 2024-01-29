from csv import DictReader
from os import path
import json
import logging

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import Ingredient


logger = logging.getLogger('import_data_to_orm')

ING_DIR = BASE_DIR / 'data'

# Для запуска не в контейнере
if not path.exists(ING_DIR):
    ING_DIR = BASE_DIR.parent.parent / 'data'


class Command(BaseCommand):
    def json_reader(self):
        reader = json.load(
            open(ING_DIR / 'ingredients.json', encoding='utf8')
        )
        self.import_ing(reader)

    def csv_reader(self):
        reader = DictReader(
            open(ING_DIR / 'ingredients.csv', encoding='utf8'),
            fieldnames=['name', 'measurement_unit']
        )
        self.import_ing(reader)

    def import_ing(self, reader):
        err_count = 0
        len_obj = 0
        logging.info('Добавление ингредиентов.')
        for row in reader:
            obj, created = Ingredient.objects.get_or_create(
                name=row['name'],
                measurement_unit=row['measurement_unit']
            )
            len_obj += 1
            if not created:
                err_count += 1
        logging.info('Количество добавленых ингредиентов: '
                     f'{len_obj - err_count} из {len_obj}.')

    def handle(self, *args, **options):
        reader_set = {
            'json': self.json_reader,
            'csv': self.csv_reader
        }
        format = input('Введите формат импортируемого файла: ')
        if format in reader_set:
            reader_set[format]()
