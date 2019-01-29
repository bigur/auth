__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from re import match, DOTALL, MULTILINE
from urllib.parse import urlparse, parse_qs

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher

from pytest import mark

from bigur.auth.authn.user_pass import BLOCK_SIZE


class TestUserPass:

    @mark.asyncio
    async def test_empty_req_auth_form(self, cli):
        response = await cli.get('/auth/login')
        assert match(r'.*<form.*>.*</form>.*', await response.text(),
                     DOTALL | MULTILINE) is not None
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert response.status == 200

    @mark.asyncio
    async def test_long_username(self, cli):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'x' * 1024,
                'password': '123',
                'next': '/auth/authorize'
            })
        assert (await response.text()) == ('400: Bad Request')
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
        assert response.status == 400

    @mark.db_configured
    @mark.asyncio
    async def test_no_such_user(self, cli, database):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'user',
                'password': '123',
                'next': '/auth/authorize'
            })
        assert match(r'.*<form.*>.*</form>.*', await response.text(),
                     DOTALL | MULTILINE) is not None
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert response.status == 200

    @mark.db_configured
    @mark.asyncio
    async def test_login_incorrect(self, cli, database):
        response = await cli.post(
            '/auth/login', data={
                'username': 'admin',
                'password': '1234'
            })
        assert match(r'.*<form.*>.*</form>.*', await response.text(),
                     DOTALL | MULTILINE) is not None
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert response.status == 200

    @mark.db_configured
    @mark.asyncio
    async def test_login_successful(self, cli, user, debug):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'admin',
                'password': '123',
                'next': '/auth/authorize?scope=openid&response_type=token_id'
            },
            allow_redirects=False)

        assert response.status == 303

        parts = urlparse(response.headers['Location'])

        assert parts.path == '/auth/authorize'

        query = parse_qs(parts.query)
        assert query == {'scope': ['openid'], 'response_type': ['token_id']}

    @mark.db_configured
    @mark.asyncio
    async def test_set_cookie(self, app, cli, user, debug):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'admin',
                'password': '123',
                'next': '/auth/authorize?scope=openid&response_type=token_id'
            },
            allow_redirects=False)

        assert response.status == 303
        assert 'Set-Cookie' in response.headers
        cookie = response.cookies['oidc']

        value = urlsafe_b64decode(cookie.value)
        iv, data = value.split(b':', maxsplit=1)

        backend = default_backend()
        cipher = Cipher(AES(app['cookie_key']), CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()
        username = unpadder.update(padded) + unpadder.finalize()

        assert username.decode('utf-8') == 'admin'

    @mark.db_configured
    @mark.asyncio
    async def test_bad_redirect_after_login(self, cli, user):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'admin',
                'password': '123',
                'next': 'http://www.disney.com/'
            },
            allow_redirects=False)

        assert response.status == 303

        parts = urlparse(response.headers['Location'])

        assert parts.path == '/http://www.disney.com/'

    @mark.db_configured
    @mark.asyncio
    async def test_login_without_next(self, cli, user, debug):
        response = await cli.post(
            '/auth/login',
            data={
                'username': 'admin',
                'password': '123',
            },
            allow_redirects=False)

        assert response.status == 200
        assert (await response.text()) == 'Login successful'

        assert 'Location' not in response.headers
