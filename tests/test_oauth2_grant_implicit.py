__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark


class TestImplicitGrant(object):
    '''Test OAuth2 implicit grant'''

    @mark.asyncio
    async def test_implicit_grant(self, auth_endpoint, user, decode_token, cli,
                                  login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'token',
                'client_id': '123',
                'scope': 'one two',
                'redirect_uri': '/response',
                'state': 'blah',
            },
            allow_redirects=False)

        assert 303 == response.status
        assert 'application/octet-stream' == response.content_type

        parsed = urlparse(response.headers['Location'])

        assert '' == parsed.scheme
        assert '' == parsed.netloc
        assert '/response' == parsed.path
        assert '' == parsed.query
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert {'access_token', 'state'} == {x for x in query.keys()}

        assert ['blah'] == query['state']

        payload = decode_token(query['access_token'][0])
        assert {'sub', 'scope'} == set(payload.keys())
        assert user.id == payload['sub']
        assert {'one', 'two'} == set(payload['scope'])

    @mark.asyncio
    async def test_extra_parameters(self, auth_endpoint, user, decode_token,
                                    cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'token',
                'client_id': '123',
                'scope': 'one two',
                'redirect_uri': '/response',
                'state': 'blah',
                'some': 'extra',
                'parameters': 'here'
            },
            allow_redirects=False)

        assert 303 == response.status

        parsed = urlparse(response.headers['Location'])
        query = parse_qs(parsed.fragment)
        assert {'access_token', 'state'} == {x for x in query.keys()}
