__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import asdict
from json import dumps, loads
from hashlib import sha256
from logging import getLogger
from pprint import pformat
from typing import List, Union
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientError
from aiohttp.web import Response
from aiohttp.web_exceptions import HTTPSeeOther, HTTPBadRequest
from aiohttp_jinja2 import render_template
from jwt import decode, get_unverified_header, DecodeError
from jwt.algorithms import get_default_algorithms
from jwt.exceptions import InvalidKeyError
from multidict import MultiDict

from bigur.auth.model.abc import AbstractProvider

from bigur.auth.authn.user.base import AuthN, crypt, decrypt

logger = getLogger(__name__)


class ProviderError(Exception):
    pass


class ConfigurationError(ProviderError):
    pass


class RegistrationNeeded(ProviderError):
    pass


class OpenIDConnect(AuthN):

    def get_domain_from_acr(self, acr_values: Union[List[str], str]) -> str:
        if isinstance(acr_values, str):
            acr_values = [x for x in acr_values.split(' ') if x]

        for acr_value in acr_values:
            parts = acr_value.split(':', 1)
            if parts[0] == 'idp':
                if len(parts) != 2:
                    raise ValueError('Invalid acr parameter')
                return parts[1]

        raise ValueError('Domain is not set in acr parameter')

    async def create_provider(self, domain: str) -> AbstractProvider:
        protocol = self.request.app['config'].get(
            'authn.oidc.provider_protocol', 'https')
        url = '{}://{}/.well-known/openid-configuration'.format(
            protocol, domain)
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
                    'Can\'t get configuration from {}: {}'.format(url, str(e)))

        if not isinstance(endpoint_cnf, dict):
            raise ConfigurationError('Invalid response while geting '
                                     'configuration for {}'.format(domain))
        logger.debug('Configuration for provider:\n%s', pformat(endpoint_cnf))

        # Set domain for endpoint
        endpoint_cnf['domains'] = [domain]

        # Set client_id & client_secret
        clients = self.request.app['config'].get('authn.oidc.clients', {})
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

    async def link_user_with_oidc(self, user_id, provider_id, subject):
        logger.debug('Linking user %s with account %s:%s', user_id, provider_id,
                     subject)
        store = self.request.app['store']
        user = await store.users.get(user_id)
        user.add_oidc_account(provider_id, subject)
        await store.users.put(user)

    @property
    def endpoint_uri(self) -> str:
        return '{}://{}{}'.format(
            self.request.scheme, self.request.host,
            self.request.app['config'].get('http_server.endpoints.oidc.path'))

    async def authenticate(self, params: MultiDict):
        request = self.request

        try:
            domain = self.get_domain_from_acr(params['acr_values'])
        except ValueError:
            logger.warning('Invalid acr_values parameter')
            raise HTTPBadRequest()

        try:
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

            nonce = sha256(request['sid'].encode('utf-8')).hexdigest()

        except ProviderError as e:
            logger.warning('Error getting provider configuration: %s', e)
            reason = str(e)
            raise HTTPSeeOther('{}?{}'.format(
                request.app['config'].get('http_server.endpoints.login.path'),
                urlencode({
                    'error':
                        'bigur_oidc_provider_error',
                    'error_description':
                        reason,
                    'next': ('{}?{}'.format(request.path,
                                            urlencode(query=params,
                                                      doseq=True))),
                })))

        else:
            raise HTTPSeeOther('{}?{}'.format(
                authorization_endpoint,
                urlencode({
                    'redirect_uri':
                        self.endpoint_uri,
                    'client_id':
                        client_id,
                    'state':
                        urlsafe_b64encode(
                            crypt(
                                request.app['cookie_key'],
                                dumps({
                                    'n': nonce,
                                    'u': request.path,
                                    'p': dict(params)
                                }))).decode('utf-8'),
                    'scope':
                        scopes,
                    'response_type':
                        'code',
                    'nonce':
                        nonce
                })))

    async def get(self) -> Response:
        request = self.request
        config = self.request.app['config']

        # Decode state parameter
        if 'state' not in request.query:
            raise HTTPBadRequest(reason='No state parameter in request')

        try:
            state = loads(
                decrypt(request.app['cookie_key'],
                        urlsafe_b64decode(request.query['state'])))

        except ValueError:
            raise HTTPBadRequest(reason='Can\'t decode state')

        logger.debug('Request state: %s', state)

        domain = self.get_domain_from_acr(state['p']['acr_values'])
        provider = await self.get_provider(domain)

        return_uri = ('{}?{}'.format(state['u'],
                                     urlencode(query=state['p'], doseq=True)))

        # There is id token in state and user authenticated, so just make
        # relationship existing user with oidc account.

        if 't' in state:
            logger.debug('Id token provided in state, checking authn')

            # Check cookie
            cookie = request.cookies.get(config.get('authn.cookie.id_name'))
            if cookie:
                logger.debug('Found authn cookie %s', cookie)
                key = request.app['cookie_key']
                userid: str = decrypt(key, urlsafe_b64decode(cookie))
                await self.link_user_with_oidc(userid, provider.id,
                                               state['t']['sub'])
                return Response(
                    status=303,
                    reason='See Other',
                    charset='utf-8',
                    headers={'Location': return_uri})
            else:
                logger.warning(
                    'Id token recieved, but authn cookie does not set')

        # Overwise it is callback with code from oidc provider
        def error_redirect(reason, source: Exception = None):
            logger.warning('Redirecting with error: %s', reason)
            exc = HTTPSeeOther('{}?{}'.format(
                request.app['config'].get('http_server.endpoints.login.path'),
                urlencode({
                    'error':
                        'bigur_oidc_provider_error',
                    'error_description':
                        reason,
                    'next': ('{}?{}'.format(
                        request.path, urlencode(query=state['p'], doseq=True))),
                })))
            if source is None:
                raise exc
            else:
                raise exc from source

        try:
            code = request.query['code']
        except KeyError as e:
            error_redirect('No code provided', e)

        try:
            token_endpoint = provider.get_token_endpoint()
        except AttributeError:
            token_endpoint = None
        if not token_endpoint:
            error_redirect('No token endpoint')

        response_types = provider.get_response_types_supported()
        if 'id_token' not in response_types:
            error_redirect('ID token not supported')

        try:
            client_id = provider.get_client_id()
            client_secret = provider.get_client_secret()
        except AttributeError as e:
            error_redirect('Invalid client credentials', e)

        logger.debug('Getting id_token from %s', token_endpoint)
        async with ClientSession() as session:
            try:
                data = {
                    'redirect_uri': self.endpoint_uri,
                    'code': code,
                    'client_id': client_id,
                    'client_secret': client_secret,
                    'grant_type': 'authorization_code'
                }
                async with session.post(token_endpoint, data=data) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error('Invalid response from provider: %s', body)
                        error_redirect('Can\'t obtain token from provider')
                    token_obj = await resp.json()

            except ClientError as e:
                error_redirect('Can\'t obtain token', e)

        if not isinstance(token_obj, dict):
            error_redirect('Invalid response from provider')

        if 'id_token' not in token_obj:
            error_redirect('Invalid response from provider')

        if str(token_obj.get('token_type', '')).lower() != 'bearer':
            error_redirect('Invalid token type returned by provider')

        try:
            header = get_unverified_header(token_obj['id_token'])
            logger.debug('Key header: %s', header)
        except DecodeError as e:
            error_redirect('Can\'t decode token', e)

        try:
            alg = get_default_algorithms()[header['alg']]
        except KeyError as e:
            logger.error('Algorythm %s is not supported', header['alg'])
            error_redirect('Key algorytm not supported', e)

        try:
            key = provider.get_key(header['kid'])
        except KeyError:
            # Key not found, update provider's keys
            try:
                await provider.update_keys()
                key = provider.get_key(header['kid'])
            except (ClientError, KeyError, TypeError) as e:
                logger.warning(str(e))
                error_redirect(
                    'Can\'t get key with kid'
                    ' {}'.format(header['kid']), e)

        try:
            key = alg.from_jwk(dumps(key))
        except InvalidKeyError as e:
            error_redirect('Can\'t decode key', e)

        try:
            # XXX: hardcoded token encryption algorithm
            payload = decode(
                token_obj['id_token'],
                key,
                audience=client_id,
                algorithms=['RS256'])
        except DecodeError as e:
            error_redirect('Can\'t decode token', e)

        logger.debug('Token id payload: %s', payload)

        if payload['nonce'] != state['n']:
            error_redirect('Can\'t verify nonce')

        if 'sub' not in payload:
            error_redirect('Invalid token')

        try:
            user = await self.request.app['store'].users.get_by_oidp(
                provider.get_id(), payload['sub'])
        except KeyError:
            logger.warning('User %s:%s not found', domain, payload['sub'])

            state['t'] = payload

            template = 'oidc_user_not_exists.j2'
            context = {
                'login_endpoint':
                    config.get('http_server.endpoints.login.path'),
                'registration_endpoint':
                    config.get('http_server.endpoints.registration.path'),
                'next':
                    config.get('http_server.endpoints.oidc.path'),
                'state':
                    urlsafe_b64encode(
                        crypt(request.app['cookie_key'],
                              dumps(state))).decode('utf-8')
            }
            return render_template(template, request, context)

        response = Response(
            status=303,
            reason='See Other',
            charset='utf-8',
            headers={'Location': return_uri})

        self.set_cookie(request, response, user.get_id())

        return response
