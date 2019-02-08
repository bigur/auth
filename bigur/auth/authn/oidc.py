__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode
from logging import getLogger
from os import urandom
from typing import Optional

from aiohttp import ClientSession, ClientError
from aiohttp.web import Request

from bigur.store import UnitOfWork
from bigur.utils import config

from bigur.auth.authn.base import AuthN
from bigur.auth.model import Provider
from bigur.auth.oauth2.rfc6749.errors import (UserNotAuthenticated,
                                              InvalidParameter)

logger = getLogger(__name__)

CLIENT_IDS = {
    'accounts.google.com':
        '164586812337-39opdhmef90m0i3saeg6udp8aee4uq7e.apps.googleusercontent.com',  # noqa
}


class ConfigurationError(Exception):
    pass


class OpenIDConnect(AuthN):

    def __init__(self, request: Request, domain: Optional[str] = None):
        self.domain = domain
        super().__init__(request)

    async def create_provider(self):
        url = 'https://{}/.well-known/openid-configuration'.format(self.domain)
        logger.debug('Getting configuration from %s', url)
        async with ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    config = await response.json()
                else:
                    raise ConfigurationError('Invalid response code: %s',
                                             response.status)
        if not isinstance(config, dict):
            raise ConfigurationError(
                'Invalid response while geting configuration for %s',
                self.domain)

        # XXX: client registration stub
        if self.domain in CLIENT_IDS:
            config['client_id'] = CLIENT_IDS[self.domain]

        async with UnitOfWork():
            return Provider(self.domain, **config)

    async def redirect_unauthenticated(self):
        provider = await Provider.find_one({'domains': self.domain})
        if provider is None:
            try:
                provider = await self.create_provider()
            except (ConfigurationError, ClientError) as e:
                logger.warning(
                    'Can\'t get configuration for %s', self.domain, exc_info=e)
                # XXX: return template
                raise NotImplementedError

        logger.debug('Using provider %s', provider)

        if not provider.authorization_endpoint:
            raise InvalidParameter('Authorization point is not defined',
                                   self.request)

        if not provider.client_id:
            raise InvalidParameter('Client does not registered', self.request)

        if (not provider.response_types_supported or
                'code' not in provider.response_types_supported):
            raise InvalidParameter('Id token not supported by provider',
                                   self.request)

        if (not provider.scopes_supported or
                'openid' not in provider.scopes_supported):
            raise InvalidParameter('Scope openid not supported by provider',
                                   self.request)

        # XXX: create auth event/session

        landing_uri = '{}://{}{}'.format(
            self.request.scheme, self.request.host,
            config.get('oidc', 'landing_endpoint', fallback='/auth/oidc'))

        scopes = ' '.join(
            list({'openid'}
                 | {'email', 'profile'} & set(provider.scopes_supported)))

        params = {
            'redirect_uri': landing_uri,
            'client_id': provider.client_id,
            'state': self.request.url,
            'scope': scopes,
            'response_type': 'code',
            'nonce': urlsafe_b64encode(urandom(16)).decode('utf-8'),
        }

        raise UserNotAuthenticated(
            'Authentication required',
            self.request,
            redirect_uri=provider.authorization_endpoint,
            params=params)

    async def get(self):
        fragment = self.request.url.fragment
        print(self.request.headers)
        print(self.request.query)

        from urllib.parse import parse_qs
        params = parse_qs(fragment)
        from pprint import pprint

        pprint(params)
        raise NotImplementedError
