__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import mark

from bigur.store import UnitOfWork
from bigur.store.test.fixtures import configured, database  # noqa: F401

from bigur.auth.model import User, Client


class TestAuthorizationEndpoint(object):
    '''Тестирование точки входа "Авторизация"'''
    @configured  # noqa: F811
    @mark.asyncio
    async def test_client_id(self, cli, database, debug):
        '''Тест проверки id клиента'''
        async with UnitOfWork():
            user = User('admin', '123')
            Client('Тестовый клиент', user.id, 'password')

            response = await cli.post('/authorize')
            text = await response.text()

            assert text == 'test'
