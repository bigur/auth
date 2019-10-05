__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict
from pytest import raises, mark

from bigur.auth.model import Client


class TestModelClient(object):
    '''Test client model'''

    @mark.asyncio
    async def test_incorrect_client_type(self, user):
        with raises(TypeError) as ei:
            Client(client_type='some_type', title='Test', user_id=user.id)
        assert ei.value.args[0] == 'Client type must be public or confidential'

    @mark.asyncio
    async def test_miss_confidential_password(self, user):
        with raises(TypeError) as ei:
            Client(client_type='confidential', title='Test', user_id=user.id)
        assert ei.value.args[0] == ('Password is required for '
                                    'confidential clients')

    @mark.asyncio
    async def test_set_password(self, user):
        client = Client(
            client_type='confidential',
            title='Test',
            user_id=user.id,
            password='123')

        assert set(asdict(client)) == {
            'id',
            'client_type',
            'user_id',
            'title',
            'redirect_uris',
            'crypt',
            'salt',
        }

        assert client.salt
        assert client.crypt
        assert client.verify_password('123')
        assert not client.verify_password('12345')

        old_salt = client.salt
        old_crypt = client.crypt
        client.set_password('12345')
        assert client.salt != old_salt
        assert client.crypt != old_crypt
        assert client.verify_password('12345')
        assert not client.verify_password('123')

    @mark.asyncio
    async def test_redirect_uri(self, user):
        client = Client(
            client_type='confidential',
            title='Test',
            user_id=user.id,
            password='123')
        assert client.redirect_uris is None
        assert not client.check_redirect_uri('http://localhost/back')

        client.redirect_uris = ['http://localhost/back', 'https://bigur.com']
        assert client.check_redirect_uri('http://localhost/back')
        assert not client.check_redirect_uri('https://gmail.com/')

    @mark.asyncio
    async def test_has_password(self, user):
        client = Client(
            client_type='public',
            title='Test',
            user_id=user.id,
        )
        assert not client.has_password()

        client.set_password('123')
        assert client.has_password()

        client.set_password(None)
        assert not client.has_password()
