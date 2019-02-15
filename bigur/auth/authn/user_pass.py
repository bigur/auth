__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Dict
from urllib.parse import urlunparse, urlencode

from aiohttp.web import Response
from aiohttp.web_exceptions import (HTTPBadRequest)
from aiohttp_jinja2 import render_template

from bigur.auth.model import User
from bigur.auth.oauth2.rfc6749.errors import UserNotAuthenticated

from bigur.auth.authn.base import AuthN

logger = getLogger(__name__)

FIELD_LENGTH = 128


class UserPass(AuthN):
    '''End-user login & password authentication'''

    async def redirect_unauthenticated(self):
        if self.request.method == 'GET':
            params = self.request.query.copy()
        elif self.request.method == 'POST':
            params = (await self.request.post()).copy()
        else:
            raise ValueError('Unsupported http method: %s', self.request.method)

        params['next'] = self.request.path
        redirect_uri = config.get(
            'user_pass', 'login_endpoint', fallback='/auth/login')
        raise UserNotAuthenticated(
            'Authentication required',
            self.request,
            redirect_uri=redirect_uri,
            params=params)

    async def get(self) -> Response:
        context: Dict[str, str] = {}
        return render_template('login_form.j2', self.request, context)

    async def post(self) -> Response:
        post = (await self.request.post()).copy()

        if ('username' in post and 'password' in post):
            # Check incoming parameters
            username = str(post.pop('username')).strip()
            password = str(post.pop('password')).strip()

            # Check fields too long
            if (len(username) > FIELD_LENGTH or len(password) > FIELD_LENGTH):
                logger.warning(
                    'Recieve request with very long login/password field')
                raise HTTPBadRequest()

            # Finding user
            logger.debug('Try to find user %s in store', username)

            user = await User.find_one({'username': username})
            if user is None:
                logger.warning('User {} not found'.format(username))
            else:
                if user.verify_password(password):
                    # Login successful
                    logger.debug('Login for user %s successful', username)

                    # No next parameter, no way to redirect
                    if 'next' not in post:
                        response = Response(text='Login successful')

                    # Redirecting
                    else:
                        next_uri = post.pop('next')
                        url = self.request.url
                        response = Response(
                            status=303,
                            reason='See Other',
                            charset='utf-8',
                            headers={
                                'Location':
                                    urlunparse(
                                        (url.scheme, url.raw_host, next_uri, '',
                                         urlencode(post, doseq=True),
                                         url.raw_fragment))
                            })
                        response.set_status(303, 'See Other')

                    # Set cookie
                    self.set_cookie(self.request, response, user.id)

                    return response

                logger.warning(
                    'Password is incorrect for user {}'.format(username))

        # Show form
        context: Dict[str, str] = {}
        return render_template('login_form.j2', self.request, context)
