'''Тестирование пользователей.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import mark

from bigur.store import UnitOfWork
from bigur.store.test.fixtures import configured, debug, database  # noqa: F401

from bigur.auth.model import User, Human


class TestUser:
    '''Тест пользователей.'''

    @configured  # noqa: F811
    @mark.asyncio
    async def test_creation(self, database):
        async with UnitOfWork():
            User('admin', '123')

        async with UnitOfWork():
            user = await User.find_one({'username': 'admin'})
            assert user.username == 'admin'

    @configured  # noqa: F811
    @mark.asyncio
    async def test_create_human(self, database):
        '''User: создание пользователя человека'''
        async with UnitOfWork():
            Human('admin', '123', first_name='Иван', patronymic='Иванович',
                  last_name='Иванов')

    @configured  # noqa: F811
    @mark.asyncio
    async def test_password(self, database):
        '''User: установка пароля'''
        async with UnitOfWork():
            user = User('admin', '123')
            assert user.verify_password('123')
            assert not user.verify_password('321')

            user.set_password('qwerty')
            assert user.verify_password('qwerty')
            assert not user.verify_password('123')
            assert not user.verify_password('ytrewq')
