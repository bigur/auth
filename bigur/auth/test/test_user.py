'''Тестирование пользователей.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from asyncio import get_event_loop
from unittest import TestCase

from bigur.config import args
from bigur.configuration import Configuration
from bigur.namespace import Namespace
from bigur.role import Role
from bigur.store import db
from bigur.user import User, Human


class TestUser(TestCase):
    '''Тест пользователей.'''
    def setUp(self):
        self.cfg = None
        self.ns = None
        self.roles = None

        self.loop = get_event_loop()
        args.set_object({})

    def tearDown(self):
        self.loop.run_until_complete(db.client.drop_database(db.name))

    async def create_configuration(self):
        '''Создание конфигурации'''
        self.cfg = await Configuration('cfg', 'Конфигурация', []).save()
        self.ns = await Namespace('Рога и Копыта', [self.cfg]).save()

    async def create_roles(self):
        '''Создание ролей'''
        self.roles = {
            'admin': await Role(1, 'admin', 'Администратор', ['all']).save()
        }

    def test_simple_creation(self):
        '''User: создание пользователя'''
        async def create(): #pylint: disable=missing-docstring
            await self.create_configuration()
            await self.create_roles()
            await User(self.ns, 'admin', '123', roles=self.roles).save()
        self.loop.run_until_complete(create())

    def test_create_human(self):
        '''User: создание пользователя человека'''
        async def create(): #pylint: disable=missing-docstring
            await self.create_configuration()
            await self.create_roles()
            await Human(self.ns, 'admin', '123', roles=self.roles,
                        name='Иван', patronymic='Иванович',
                        surname='Иванов').save()
        self.loop.run_until_complete(create())

    def test_password(self):
        '''User: установка пароля'''
        async def set_password(): #pylint: disable=missing-docstring
            await self.create_configuration()
            await self.create_roles()

            admin = await User(self.ns, 'admin', '123', roles=self.roles).save()
            self.assertTrue(admin.verify_password('123'))
            self.assertFalse(admin.verify_password('321'))

            admin.set_password('qwerty')
            self.assertTrue(admin.verify_password('qwerty'))
            self.assertFalse(admin.verify_password('123'))
            self.assertFalse(admin.verify_password('ytrewq'))
        self.loop.run_until_complete(set_password())
