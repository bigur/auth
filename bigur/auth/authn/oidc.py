__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import asdict
from json import dumps, loads
from hashlib import sha256
from logging import getLogger
from typing import Dict, List, Union
from urllib.parse import parse_qs, urlencode

from aiohttp import ClientSession, ClientError
from aiohttp.web import Response
from aiohttp.web_exceptions import (HTTPSeeOther, HTTPBadRequest,
                                    HTTPUnauthorized)
from aiohttp_jinja2 import render_template
from jwt import decode, get_unverified_header, DecodeError
from jwt.algorithms import get_default_algorithms
from jwt.exceptions import InvalidKeyError

from bigur.auth.authn.base import AuthN, crypt, decrypt
from bigur.auth.model.abc import AbstractProvider
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

    async def create_provider(self, domain: str) -> AbstractProvider:
        url = 'https://{}/.well-known/openid-configuration'.format(domain)
        logger.debug('Getting configuration from %s', url)
        async with ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        endpoint_cnf = await resp.json()
                    else:
                        raise ConfigurationError(
                            'Can\'t get configuration from {}: '
                            'response code is {}'.format(url, resp.status))
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

    async def get_provider(self, domain: str) -> AbstractProvider:
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
        req = self.request
        areq = req['oauth2_request']
        try:
            domain = self.domain_from_acr_values(areq.acr_values)
        except ValueError as e:
            raise InvalidParameter(str(e), req)

        try:
            params = {k: v for k, v in asdict(areq).items() if v is not None}

            provider = await self.get_provider(domain)

            logger.debug('Using provider %s', provider)

            authorization_endpoint = provider.get_authorization_endpoint()
            if not authorization_endpoint:
                raise ConfigurationError('Authorization point is not defined')

            client_id = provider.get_client_id()
            if not client_id:
                raise ConfigurationError('Client does not registered')

            if 'code' not in provider.get_response_types_supported():
                raise ConfigurationError(
                    'Responce type "code" is not supported by provider')

            scopes = provider.get_scopes_supported()
            if 'openid' not in scopes:
                raise ConfigurationError(
                    'Scope "openid" is not supported by provider')
            scopes = ' '.join(
                list({'openid'} | {'email', 'profile'} & set(scopes)))

            key = req.app['cookie_key']
            sid = req['sid']
            nonce = sha256(req['sid'].encode('utf-8')).hexdigest()
            state = crypt(
                key, dumps({
                    's': sid,
                    'n': nonce,
                    'u': req.path,
                    'p': params
                }))

        except ProviderError as e:
            reason = str(e)
            redirect_uri = req.app['config'].get(
                'http_server.endpoints.login.path')

            raise UserNotAuthenticated(
                reason,
                req,
                redirect_uri=redirect_uri,
                params={
                    'error':
                        'bigur_oidc_provider_error',
                    'error_description':
                        reason,
                    'next': ('{}/{}'.format(req.path,
                                            urlencode(query=params,
                                                      doseq=True)))
                })

        else:
            raise UserNotAuthenticated(
                'Authentication required',
                req,
                redirect_uri=authorization_endpoint,
                params={
                    'redirect_uri': self.endpoint_uri,
                    'client_id': client_id,
                    'state': urlsafe_b64encode(state).decode('utf-8'),
                    'scope': scopes,
                    'response_type': 'code',
                    'nonce': nonce
                })

    async def get(self) -> Response:
        req = self.request
        if 'state' not in req.query:
            raise HTTPBadRequest(reason='No state parameter in request')

        try:
            state = loads(
                decrypt(req.app['cookie_key'],
                        urlsafe_b64decode(req.query['state'])).decode('utf-8'))

        except ValueError:
            raise HTTPBadRequest(reason='Can\'t decode state')

        if state['s'] != req['sid']:
            raise HTTPUnauthorized(reason='Authentication required')

        logger.debug('First request parameters: %s', state['p'])

        try:
            try:
                code = req.query['code']
            except KeyError:
                raise InvalidParameter('No code provided', req)

            domain = self.domain_from_acr_values(state['p']['acr_values'][0])
            provider = await self.get_provider(domain)

            token_endpoint = provider.get_token_endpoint()
            if token_endpoint is None:
                raise InvalidParameter('Provider has no token endpoint', req)

            response_types = provider.get_response_types_supported()
            if ('id_token' not in response_types):
                raise InvalidParameter('Id token not supported by provider',
                                       req)

            client_id = provider.get_client_id()
            client_secret = provider.get_client_secret()

            data = {
                'redirect_uri': self.endpoint_uri,
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'grant_type': 'authorization_code'
            }

            logger.debug('Getting id_token from %s', token_endpoint)
            async with ClientSession() as session:
                try:
                    async with session.post(token_endpoint, data=data) as resp:
                        if resp.status != 200:
                            body = await resp.text()
                            logger.error('Invalid response from provider: %s',
                                         body)
                            raise InvalidParameter(
                                'Can\'t obtain token: {}'.format(resp.status),
                                self.request)
                        data = await resp.json()
                        if 'id_token' not in data:
                            raise InvalidParameter('Provider not return token',
                                                   req)
                except ClientError:
                    raise InvalidParameter('Can\'t get token', req)

            if str(data.get('token_type', '')).lower() != 'bearer':
                raise InvalidParameter('Invalid token type provided', req)

            try:
                header = get_unverified_header(data['id_token'])
                logger.debug('Key header: %s', header)
            except DecodeError:
                raise InvalidParameter('Can\'t decode token', req)

            try:
                alg = get_default_algorithms()[header['alg']]
            except KeyError:
                logger.error('Algorythm %s is not supported', header['alg'])
                raise InvalidParameter('Key algorytm not supported', req)

            try:
                key = provider.get_key(header['kid'])
            except KeyError:
                # Key not found, update provider's keys
                try:
                    await provider.update_keys()
                    key = provider.get_key(header['kid'])
                except (ClientError, KeyError) as e:
                    logger.warning(str(e))
                    raise InvalidParameter(
                        'Can\'t get key with kid'
                        ' {}'.format(header['kid']), req)

            try:
                key = alg.from_jwk(dumps(key))
            except InvalidKeyError:
                raise InvalidParameter('Can\'t decode key', req)

            try:
                payload = decode(data['id_token'], key, audience=client_id)
            except DecodeError:
                raise InvalidParameter('Can\'t decode token', req)

            logger.debug('Token id payload: %s', payload)

            if payload['nonce'] != state['n']:
                raise InvalidParameter('Can\'t verify nonce', req)

            if 'sub' not in payload:
                raise InvalidParameter('Invalid token', req)

        except InvalidParameter as e:
            raise HTTPSeeOther('{}?{}'.format(
                self.request.app['config'].get(
                    'http_server.endpoints.login.path'),
                urlencode({
                    'error':
                        'bigur_oidc_provider_error',
                    'error_description':
                        str(e),
                    'next': ('{}?{}'.format(state['u'],
                                            urlencode(state['p'], doseq=True)))
                })))

        else:
            try:
                user = await self.request.app['store'].users.get_by_oidp(
                    provider.get_id(), payload['sub'])
            except KeyError:
                logger.warning('User %s:%s not found', domain, payload['sub'])
                context: Dict[str, str] = {}
                return render_template('oidc_user_not_exists.j2', req, context)

        response = Response(
            status=303,
            reason='See Other',
            charset='utf-8',
            headers={'Location': return_uri})

        self.set_cookie(req, response, user.get_id())

        return response
