__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode, urlsafe_b64decode
from hashlib import sha256
from logging import getLogger
from typing import List, Union
from urllib.parse import parse_qs

from aiohttp import ClientSession, ClientError
from aiohttp.web_exceptions import HTTPSeeOther
from aiohttp.web import Response
from jwt import decode, get_unverified_header
from jwt.algorithms import get_default_algorithms

from bigur.store import UnitOfWork
from bigur.utils import config

from bigur.auth.authn.base import AuthN, crypt, decrypt
from bigur.auth.model import Provider
from bigur.auth.oauth2.rfc6749.errors import (
    UserNotAuthenticated, InvalidParameter, InvalidClientCredentials)

from bigur.auth.model import User

logger = getLogger(__name__)


class ProviderError(Exception):
    pass


class ConfigurationError(ProviderError):
    pass


class RegistrationNeeded(ProviderError):
    pass


class OpenIDConnect(AuthN):

    def domain_from_acr_values(self, acr_values: Union[List[str], str]) -> str:
        if isinstance(acr_values, str):
            acr_values = [x for x in acr_values.split(' ') if x]

        for acr_value in acr_values:
            parts = acr_value.split(':')
            if parts[0] == 'idp':
                if len(parts) != 2:
                    raise ValueError('Invalid acr value')
                return parts[1]

        raise ValueError('Domain is not set')

    async def create_provider(self, domain: str) -> Provider:
        url = 'https://{}/.well-known/openid-configuration'.format(domain)
        logger.debug('Getting configuration from %s', url)
        async with ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        endpoint_cnf = await response.json()
                    else:
                        raise ConfigurationError(
                            'Can\'t get configuration from {}: '
                            'response code is {}'.format(url, response.status))
            except ConfigurationError as e:
                raise ProviderError(
                    'Can\'t get configuration from {}: '
                    '{}'.format(url), str(e))

        if not isinstance(endpoint_cnf, dict):
            raise ConfigurationError('Invalid response while geting '
                                     'configuration for {}'.format(domain))

        # Well known providers
        try:
            endpoint_cnf['client_id'] = config.get(
                'oidc', '{}_client_id'.format(domain))
            endpoint_cnf['client_secret'] = config.get(
                'oidc', '{}_client_secret'.format(domain))
        except ValueError:
            raise RegistrationNeeded(
                'Provider {} is not supported'.format(domain))

        async with UnitOfWork():
            return Provider(domain, **endpoint_cnf)

    async def get_provider(self, domain: str) -> Provider:
        provider = await Provider.find_one({'domains': domain})
        if provider is None:
            provider = await self.create_provider(domain)
        return provider

    @property
    def landing_uri(self) -> str:
        return '{}://{}{}'.format(
            self.request.scheme, self.request.host,
            config.get('oidc', 'landing_endpoint', fallback='/auth/oidc'))

    async def redirect_unauthenticated(self):

        try:
            domain = self.domain_from_acr_values(
                self.request['oauth2_request'].acr_values)
        except ValueError as e:
            raise InvalidParameter(str(e), self.request)

        try:
            provider = await self.get_provider(domain)
        except ProviderError as e:
            raise InvalidClientCredentials(str(e))

        logger.debug('Using provider %s', provider)

        if not provider.authorization_endpoint:
            raise InvalidParameter('Authorization point is not defined',
                                   self.request)

        if not provider.client_id:
            raise InvalidParameter('Client does not registered', self.request)

        if (not provider.response_types_supported or
                'code' not in provider.response_types_supported):
            raise InvalidParameter('Code not supported by provider',
                                   self.request)

        if (not provider.scopes_supported or
                'openid' not in provider.scopes_supported):
            raise InvalidParameter('Scope openid not supported by provider',
                                   self.request)

        scopes = ' '.join(
            list({'openid'}
                 | {'email', 'profile'} & set(provider.scopes_supported)))

        key = self.request.app['cookie_key']
        sid = self.request['sid']
        nonce = sha256(self.request['sid'].encode('utf-8')).hexdigest()
        state = crypt(key, '{}|{}|{}'.format(sid, nonce, str(self.request.url)))
        params = {
            'redirect_uri': self.landing_uri,
            'client_id': provider.client_id,
            'state': urlsafe_b64encode(state).decode('utf-8'),
            'scope': scopes,
            'response_type': 'code',
            'nonce': nonce,
        }

        raise UserNotAuthenticated(
            'Authentication required',
            self.request,
            redirect_uri=provider.authorization_endpoint,
            params=params)

    async def get(self) -> Response:
        if 'state' not in self.request.query:
            raise InvalidParameter('No state parameter in request',
                                   self.request)

        try:
            state = decrypt(self.request.app['cookie_key'],
                            urlsafe_b64decode(
                                self.request.query['state'])).decode('utf-8')

        except ValueError:
            raise InvalidParameter('Can\'t decode state', self.request)

        sid, nonce, uri = state.split('|')
        if sid != self.request['sid']:
            # XXX: use correct exception
            raise InvalidParameter('Authentication required', self.request)

        if 'code' not in self.request.query:
            raise InvalidParameter('No code provided', self.request)

        code = self.request.query['code']

        params = parse_qs(uri)
        logger.debug(params)

        try:
            domain = self.domain_from_acr_values(params['acr_values'][0])
        except ValueError:
            raise InvalidParameter('Can\'t parse domain',
                                   self.request)  # XXX: Bad request
        provider = await self.get_provider(domain)
        if provider.token_endpoint is None:
            # XXX: use proper exception class
            raise InvalidParameter('Provider has no token endpoint',
                                   self.request)

        if (not provider.response_types_supported or
                'id_token' not in provider.response_types_supported):
            raise InvalidParameter('Id token not supported by provider',
                                   self.request)

        data = {
            'redirect_uri': self.landing_uri,
            'code': code,
            'client_id': provider.client_id,
            'client_secret': provider.client_secret,
            'grant_type': 'authorization_code'
        }

        logger.debug('Getting id_token from %s', provider.token_endpoint)
        async with ClientSession() as session:
            try:
                async with session.post(
                        provider.token_endpoint, data=data) as response:
                    if response.status != 200:
                        body = await response.text()
                        logger.error('Invalid response from provider: %s', body)
                        raise InvalidParameter(
                            'Can\'t obtain token: {}'.format(response.status),
                            self.request)
                    data = await response.json()
                    if 'id_token' not in data:
                        raise InvalidParameter('Provider not return token',
                                               self.request)
            except ClientError:
                raise InvalidParameter('Ca\'t get token', self.request)

        if str(data.get('token_type', '')).lower() != 'bearer':
            raise InvalidParameter('Invalid token type provided', self.request)

        header = get_unverified_header(data['id_token'])
        alg = get_default_algorithms()[header['alg']]
        key = await provider.get_key(header['kid'])
        from json import dumps
        key = alg.from_jwk(dumps(key))

        payload = decode(data['id_token'], key, audience=provider.client_id)
        logger.debug(payload)

        if payload['nonce'] != nonce:
            raise InvalidParameter('Can\'t verify nonce', self.request)

        user = await User.find_one({
            'accounts.provider': provider.id,
            'accounts.id': payload['sub']
        })
        if user is None:
            logger.warning('User {} not found'.format(payload['sub']))
            url = '{}://{}{}'.format(
                self.request.scheme, self.request.host,
                config.get(
                    'oidc', 'register_endpoint', fallback='/auth/register'))
            raise HTTPSeeOther(location=url)

        return Response(text='ok')
