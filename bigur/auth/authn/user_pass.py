__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from urllib.parse import urlunparse, urlencode

from aiohttp.web import Response
from aiohttp.web_exceptions import (HTTPBadRequest)
from aiohttp_jinja2 import render_template

from bigur.auth.oauth2.rfc6749.errors import UserNotAuthenticated

from bigur.auth.authn.base import AuthN

logger = getLogger(__name__)

FIELD_LENGTH = 128


class UserPass(AuthN):
    '''End-user login & password authentication'''

    async def authenticate(self):
        request = self.request
        params = request['oauth2_request'].asdict()
        params['next'] = request.path
        redirect_uri = request.app['config'].get(
            'http_server.endpoints.login.path')
        raise UserNotAuthenticated(
            'Authentication required',
            request,
            redirect_uri=redirect_uri,
            params=params)

    async def get(self) -> Response:
        config = self.request.app['config']
        query = self.request.query
        context = {
            'endpoint': config.get('http_server.endpoints.login.path'),
            'query': query,
            'error': query.get('error'),
            'error_description': query.get('error_description'),
        }
        return render_template('login_form.j2', self.request, context)

    async def post(self) -> Response:
        query = (await self.request.post()).copy()

        error = None
        error_description = None

        if ('username' in query and 'password' in query):
            # Check incoming parameters
            username = str(query.pop('username')).strip()
            password = str(query.pop('password')).strip()

            # Check fields too long
            if (len(username) > FIELD_LENGTH or len(password) > FIELD_LENGTH):
                logger.warning(
                    'Recieve request with very long login/password field')
                raise HTTPBadRequest()

            # Finding user
            logger.debug('Try to find user %s in store', username)

            try:
                user = self.request.app['store'].users.get_by_username(username)
            except KeyError:
                logger.warning('User {} not found'.format(username))
                error = 'bigur_invalid_login'
                error_description = 'Invalid login or password'
            else:
                if user.verify_password(password):
                    # Login successful
                    logger.debug('Login for user %s successful', username)

                    # No next parameter, no way to redirect
                    if 'next' not in query:
                        response = Response(text='Login successful')

                    # Redirecting
                    else:
                        next_uri = query.pop('next')
                        url = self.request.url
                        response = Response(
                            status=303,
                            reason='See Other',
                            charset='utf-8',
                            headers={
                                'Location':
                                    urlunparse(
                                        (url.scheme, url.raw_host, next_uri, '',
                                         urlencode(query, doseq=True),
                                         url.raw_fragment))
                            })

                    # Set cookie
                    self.set_cookie(self.request, response, user.id)

                    return response

                logger.warning(
                    'Password is incorrect for user {}'.format(username))
                error = 'bigur_invalid_login'
                error_description = 'Invalid login or password'

        # Show form
        context = {
            'endpoint':
                self.request.app['config'].get(
                    'http_server.endpoints.login.path'),
            'query':
                query,
            'error':
                error,
            'error_description':
                error_description
        }
        return render_template('login_form.j2', self.request, context)
