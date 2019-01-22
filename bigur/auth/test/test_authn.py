__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from re import match, DOTALL, MULTILINE
from pytest import mark


class TestUserPass:

    @mark.asyncio
    async def test_empty_req_auth_form(self, cli):
        response = await cli.get('/authorize?client_id=blah')
        assert match(r'.*<form.*>.*</form>.*',
                     await response.text(),
                     DOTALL | MULTILINE) is not None
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert response.status == 200

    @mark.asyncio
    async def test_long_username(self, cli, debug):
        response = await cli.post('/login', data={'username': 'x' * 1024,
                                                  'password': '123'})
        assert match(r'.*HTTP\sStatus\sCode:\s400.*',
                     await response.text(),
                     DOTALL | MULTILINE) is not None
        assert response.headers['Content-Type'] == 'text/html; charset=utf-8'
        assert response.status == 200
