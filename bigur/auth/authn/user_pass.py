__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Any, Dict, Optional, cast
from urllib.parse import urlparse, urlencode

from aiohttp.web import Response, json_response
from aiohttp.web_exceptions import (HTTPBadRequest, HTTPSeeOther)
from aiohttp_jinja2 import render_template
from multidict import MultiDict

from bigur.auth.authn.base import AuthN
from bigur.auth.utils import choice_content_type, parse_accept

logger = getLogger(__name__)

FIELD_LENGTH = 128


class UserPass(AuthN):
    '''End-user login & password authentication'''

    async def authenticate(self):
        request = self.request
        params = request['params']
        logger.debug('Redirecting to login form')
        raise HTTPSeeOther(location='{}?{}'.format(
            request.app['config'].get('http_server.endpoints.login.path'),
            urlencode({
                'next': '{}?{}'.format(request.path, urlencode(params))
            })))

    async def get(self) -> Response:
        config = self.request.app['config']
        query = self.request.query
        context = {
            'endpoint': config.get('http_server.endpoints.login.path'),
            'query': query,
            'error': query.get('error'),
            'error_description': query.get('error_description'),
        }
        logger.debug('Returning login form')
        return render_template('login_form.j2', self.request, context)

    async def post(self) -> Response:
        request = self.request
        ctype = request.headers.get('content-type')

        logger.debug('Request Content-Type: %s', ctype)

        form: MultiDict

        if ctype == 'application/json':
            try:
                data: Any = await request.json()
                if not isinstance(data, dict):
                    raise ValueError('Invalid request type')
            except ValueError as e:
                logger.warning('Invalid request: %s', e)
                raise HTTPBadRequest(reason='Invalid request') from e
            else:
                form = MultiDict(cast(Dict, data))

        elif ctype == 'application/x-www-form-urlencoded':
            form = (await self.request.post()).copy()

        else:
            raise HTTPBadRequest(reason='Invalid content type')

        logger.debug('Form is: %s', form)

        accepts = parse_accept(request.headers.get('Accept'))
        response_ctype = choice_content_type(accepts,
                                             ['application/json', 'text/plain'])
        logger.debug('Content-type for response is: %s', response_ctype)

        error: Optional[str] = None
        error_description: Optional[str] = None

        if ('username' in form and 'password' in form):
            # Check incoming parameters
            username = str(form.pop('username')).strip()
            password = str(form.pop('password')).strip()

            # Check fields too long
            if (len(username) > FIELD_LENGTH or len(password) > FIELD_LENGTH):
                logger.warning(
                    'Recieve request with very long login/password field')
                raise HTTPBadRequest()

            # Ensure no redirect to external host
            next_uri = form.get('next')
            if next_uri:
                parsed = urlparse(next_uri)
                if parsed.scheme or parsed.netloc:
                    logger.warning('Trying to do external redirect')
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

                    if response_ctype == 'application/json':
                        response = json_response({'meta': {'status': 'ok'}})
                    else:
                        # No next parameter, no way to redirect
                        if not next_uri:
                            response = Response(text='Login successful')

                        # Redirecting
                        else:
                            response = Response(
                                status=303,
                                reason='See Other',
                                charset='utf-8',
                                headers={'Location': next_uri})

                    # Set cookie
                    self.set_cookie(self.request, response, user.id)

                    return response

                logger.warning(
                    'Password is incorrect for user {}'.format(username))
                error = 'bigur_invalid_login'
                error_description = 'Invalid login or password'

        if response_ctype == 'application/json':
            return json_response({
                'meta': {
                    'status': 'error',
                    'error': error,
                    'message': error_description
                }
            })
        else:
            # Show form
            context = {
                'endpoint':
                    self.request.app['config'].get(
                        'http_server.endpoints.login.path'),
                'query':
                    form,
                'error':
                    error,
                'error_description':
                    error_description,
                'prefix':
                    request.app['config'].get('http_server.static.prefix', '/')
            }
            return render_template('login_form.j2', self.request, context)
