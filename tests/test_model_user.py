__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark


class TestModelUser(object):
    '''Test user model'''

    @mark.asyncio
    async def test_create(self):
        raise NotImplementedError

    @mark.asyncio
    async def test_password_init(self):
        user = User('admin', '123')
        assert user.verify_password('123')

    @mark.asyncio
    async def test_set_password(self):
        user = User('admin')
        user.set_password('1234')
        assert user.verify_password('1234')

    @mark.asyncio
    async def test_invalid_password(self):
        user = User('admin', '123')
        assert not user.verify_password('1234')

    @mark.asyncio
    async def test_create_human(self):
        Human(
            'admin',
            '123',
            given_name='Ivan',
            patronymic='Ivanovich',
            family_name='Ivanov')
