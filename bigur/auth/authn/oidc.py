__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import asdict
from json import dumps
from hashlib import sha256
from logging import getLogger
from typing import Dict, List, Union
from urllib.parse import parse_qs, urlencode

from aiohttp import ClientSession, ClientError
from aiohttp.web import Response
from aiohttp.web_exceptions import HTTPBadRequest, HTTPUnauthorized
from aiohttp_jinja2 import render_template
from jwt import decode, get_unverified_header, DecodeError
from jwt.algorithms import get_default_algorithms
from jwt.exceptions import InvalidKeyError

from bigur.auth.authn.base import AuthN, crypt, decrypt
from bigur.auth.model.abc import Provider
from bigur.auth.oauth2.rfc6749.errors import (UserNotAuthenticated,
                                              InvalidParameter)

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
                    raise ValueError('Invalid acr parameter')
                return parts[1]

        raise ValueError('Domain is not set in acr parameter')

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
            except ClientError as e:
                raise ConfigurationError(
                    'Can\'t get configuration from {}: '
                    '{}'.format(url), str(e))

        if not isinstance(endpoint_cnf, dict):
            raise ConfigurationError('Invalid response while geting '
                                     'configuration for {}'.format(domain))

        # Set domain for endpoint
        endpoint_cnf['domains'] = [domain]

        # Set client_id & client_secret
        clients = self.request.app['config'].get('authn.oidc.clients')
        if domain in clients:
            # Client settings are in config file
            logger.debug('Client config for domain %s: %s', domain,
                         clients[domain])
            endpoint_cnf['client_id'] = clients[domain]['client_id']
            endpoint_cnf['client_secret'] = clients[domain]['client_secret']

        else:
            # Unknown provider
            # TODO: dynamic client registration
            raise RegistrationNeeded(
                'Provider {} is not supported'.format(domain))

        return await self.request.app['store'].providers.create(**endpoint_cnf)

    async def get_provider(self, domain: str) -> Provider:
        try:
            provider = await self.request.app['store'].providers.get_by_domain(
                domain)
        except KeyError:
            provider = await self.create_provider(domain)
        return provider

    @property
    def endpoint_uri(self) -> str:
        return '{}://{}{}'.format(
            self.request.scheme, self.request.host,
            self.request.app['config'].get('http_server.endpoints.oidc.path'))

    async def authenticate(self):
        try:
            domain = self.domain_from_acr_values(
                self.request['oauth2_request'].acr_values)
        except ValueError as e:
            raise InvalidParameter(str(e), self.request)

        try:
            provider = await self.get_provider(domain)

            logger.debug('Using provider %s', provider)

            authorization_endpoint = await provider.get_authorization_endpoint()
            if not authorization_endpoint:
                raise ConfigurationError('Authorization point is not defined')

            client_id = provider.get_client_id()
            if not await client_id:
                raise ConfigurationError('Client does not registered')

            if 'code' not in await provider.get_response_types_supported():
                raise ConfigurationError(
                    'Responce type "code" is not supported by provider')

            scopes = await provider.get_scopes_supported()
            if 'openid' not in scopes:
                raise ConfigurationError(
                    'Scope "openid" is not supported by provider')
            scopes = ' '.join(
                list({'openid'} | {'email', 'profile'} & set(scopes)))

            key = self.request.app['cookie_key']
            sid = self.request['sid']
            nonce = sha256(self.request['sid'].encode('utf-8')).hexdigest()
            # XXX: what about POST method?
            state = crypt(key, '{}|{}|{}'.format(sid, nonce,
                                                 str(self.request.url)))
            params = {
                'redirect_uri': self.landing_uri,
                'client_id': client_id,
                'state': urlsafe_b64encode(state).decode('utf-8'),
                'scope': scopes,
                'response_type': 'code',
                'nonce': nonce
            }

        except ProviderError as e:
            reason = str(e)
            next_url = '{}?{}'.format(
                self.request.path,
                urlencode({
                    k: v
                    for k, v in asdict(self.request['oauth2_request']).items()
                    if v is not None
                }))
            params = {
                'error': 'bigur_oidc_provider_error',
                'error_description': reason,
                'next': next_url
            }
            redirect_uri = self.request.app['config'].get(
                'http_server.endpoints.login.path')

            raise UserNotAuthenticated(
                reason, self.request, redirect_uri=redirect_uri, params=params)

        else:
            raise UserNotAuthenticated(
                'Authentication required',
                self.request,
                redirect_uri=authorization_endpoint,
                params=params)

    async def get(self) -> Response:
        if 'state' not in self.request.query:
            raise HTTPBadRequest(reason='No state parameter in request')

        try:
            state = decrypt(self.request.app['cookie_key'],
                            urlsafe_b64decode(
                                self.request.query['state'])).decode('utf-8')

        except ValueError:
            raise HTTPBadRequest(reason='Can\'t decode state')

        sid, nonce, uri = state.split('|')
        if sid != self.request['sid']:
            raise HTTPUnauthorized(reason='Authentication required')

        params = parse_qs(uri)
        logger.debug(params)

        try:
            if 'code' not in self.request.query:
                raise InvalidParameter('No code provided', self.request)

            code = self.request.query['code']

            try:
                domain = self.domain_from_acr_values(params['acr_values'][0])
            except ValueError:
                raise InvalidParameter('Can\'t parse domain', self.request)

            provider = await self.get_provider(domain)

            token_endpoint = await provider.get_token_endpoint()
            if token_endpoint is None:
                raise InvalidParameter('Provider has no token endpoint',
                                       self.request)

            response_types = await provider.get_response_types_supported()
            if ('id_token' not in response_types):
                raise InvalidParameter('Id token not supported by provider',
                                       self.request)

            client_id = await provider.get_client_id()
            client_secret = await provider.get_client_secret()

            data = {
                'redirect_uri': self.landing_uri,
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code'
            }

            logger.debug('Getting id_token from %s', token_endpoint)
            async with ClientSession() as session:
                try:
                    async with session.post(
                            token_endpoint, data=data) as response:
                        if response.status != 200:
                            body = await response.text()
                            logger.error('Invalid response from provider: %s',
                                         body)
                            raise InvalidParameter(
                                'Can\'t obtain token: {}'.format(
                                    response.status), self.request)
                        data = await response.json()
                        if 'id_token' not in data:
                            raise InvalidParameter('Provider not return token',
                                                   self.request)
                except ClientError:
                    raise InvalidParameter('Ca\'t get token', self.request)

            if str(data.get('token_type', '')).lower() != 'bearer':
                raise InvalidParameter('Invalid token type provided',
                                       self.request)

            try:
                header = get_unverified_header(data['id_token'])
            except DecodeError:
                raise InvalidParameter('Can\'t decode token', self.request)

            try:
                alg = get_default_algorithms()[header['alg']]
                key = await provider.get_key(header['kid'])
            except KeyError:
                raise InvalidParameter('Can\'t detect key id', self.request)

            try:
                key = alg.from_jwk(dumps(key))
            except InvalidKeyError:
                raise InvalidParameter('Can\'t decode key', self.request)

            try:
                payload = decode(data['id_token'], key, audience=client_id)
            except DecodeError:
                raise InvalidParameter('Can\'t decode token', self.request)

            logger.debug('Token id payload: %s', payload)

            if payload['nonce'] != nonce:
                raise InvalidParameter('Can\'t verify nonce', self.request)

            if 'sub' not in payload:
                raise InvalidParameter('Invalid token', self.request)

            try:
                provider_id = await provider.get_id()
                user = await self.request.app['store'].users.get_by_oidp(
                    provider_id, payload['sub'])
            except KeyError:
                logger.warning('User {} not found'.format(payload['sub']))
                context: Dict[str, str] = {}
                return render_template('oidc_user_not_exists.j2', self.request,
                                       context)

        except InvalidParameter as e:
            pass
        return Response(text='ok')
