'''Модуль тестирования сессии.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from asyncio import get_event_loop
from unittest import TestCase

from bigur.config import args
from bigur.configuration import Configuration
from bigur.namespace import Namespace
from bigur.role import Role
from bigur.session import Session
from bigur.store import db
from bigur.user import User, Human


class TestConfiguration(TestCase):
    '''Тест сессии.'''
    def setUp(self):
        self.loop = get_event_loop()
        args.set_object({})

    def tearDown(self):
        self.loop.run_until_complete(db.client.drop_database(db.name))

    def test_simple_creation(self):
        '''Session: создание сессии'''
        async def create(): #pylint: disable=missing-docstring
            cfg = await Configuration('cfg', 'Конфигурация', []).save()
            ns = await Namespace('Рога и Копыта', [cfg]).save()
            role = await Role(1, 'admin', 'Администратор', ['all']).save()
            user = await User(ns, 'admin', '123', [ns], [role]).save()
            await Session(user, '127.0.0.1', 'Mozilla/...').save()
        self.loop.run_until_complete(create())
