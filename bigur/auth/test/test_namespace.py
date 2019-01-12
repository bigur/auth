'''Тестирование пространства имён.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from asyncio import get_event_loop
from unittest import TestCase

from bigur.config import args
from bigur.configuration import Configuration
from bigur.namespace import Namespace
from bigur.store import db


class TestNamespace(TestCase):
    '''Тест пространтсва имён.'''
    def setUp(self):
        self.loop = get_event_loop()
        args.set_object({})

    def tearDown(self):
        self.loop.run_until_complete(db.client.drop_database(db.name))

    def test_simple_creation(self):
        '''Namespace: создание пространства имён'''
        async def create(): #pylint: disable=missing-docstring
            cfg = await Configuration('cfg', 'Конфигурация', []).save()
            await Namespace('Рога и Копыта', [cfg]).save()
        self.loop.run_until_complete(create())
