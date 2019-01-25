__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import mark


class TestOIDCAuthorizationEndpoint(object):
    '''Tests for authorization endpoint'''

    @mark.db_configured
    @mark.asyncio
    async def test_no_scope_in_request(self, cli):
        response = await cli.post('/authorize', data={
            'client_id': 'incorrect',
            'response_type': 'token_id',
            'redirect_uri': 'https://localhost/',
        })

        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert (await response.text() ==
                '400: Missing 1 required argument: \'scope\'')

    @mark.db_configured
    @mark.asyncio
    async def test_ignore_other_params(self, cli, debug):
        response = await cli.post('/authorize', data={
            'client_id': 'incorrect',
            'scope': 'openid',
            'response_type': 'token_id',
            'redirect_uri': 'https://localhost/',
            'other': 'must_be_ignored'
        })

        assert response.status == 200
        assert response.content_type == 'text/plain'
        assert (await response.text() ==
                '400: Missing 1 required argument: \'scope\'')


    @mark.db_configured
    @mark.asyncio
    async def test_incorrect_client_id(self, cli, debug):
        response = await cli.post('/authorize', data={
            'scope': 'openid',
            'client_id': 'incorrect',
            'response_type': 'token_id',
            'redirect_uri': 'https://localhost/',
        })

        assert response.status == 400
        assert response.content_type == 'text/plain; charset=utf-8'
        assert await response.text == 'Incorrect client_id.'
