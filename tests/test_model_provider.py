__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import mark

from bigur.auth.model import Provider


class TestProvider(object):

    @mark.asyncio
    async def test_creation(self):
        Provider(
            issuer='https://accounts.google.com',
            authorization_endpoint=('https://accounts.google.com'
                                    '/o/oauth2/v2/auth'),
            token_endpoint='https://oauth2.googleapis.com/token',
            userinfo_endpoint=('https://openidconnect.googleapis.com'
                               '/v1/userinfo'),
            revocation_endpoint='https://oauth2.googleapis.com/revoke',
            jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
            response_types_supported=[
                'code', 'token', 'id_token', 'code token', 'code id_token',
                'token id_token', 'code token id_token', 'none'
            ],
            subject_types_supported=['public'],
            id_token_signing_alg_values_supported=['RS256'],
            scopes_supported=['openid', 'email', 'profile'],
            token_endpoint_auth_methods_supported=[
                'client_secret_post', 'client_secret_basic'
            ],
            claims_supported=[
                'aud', 'email', 'email_verified', 'exp', 'family_name',
                'given_name', 'iat', 'iss', 'locale', 'name', 'picture', 'sub'
            ],
            code_challenge_methods_supported=['plain', 'S256'],
            domains=['accounts.google.com'],
            client_id='123',
            client_secret='xxx')
