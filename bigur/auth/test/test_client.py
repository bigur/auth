__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import mark

from bigur.store import UnitOfWork
from bigur.store.test.fixtures import configured, database  # noqa: F401

from bigur.auth.model import Client, User


class TestClient(object):
    '''Тестирование клиента'''
    @configured  # noqa: F811
    @mark.asyncio
    async def test_creation(self, database):
        '''Простое создание клиента'''
        async with UnitOfWork():
            user = User('admin', '123')
            Client('Тестовый клиент', user.id, 'password')
