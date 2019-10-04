'''User registration module.'''

__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import Any, Dict, cast
from urllib.parse import urlencode

from aiohttp.web import Response, json_response
from aiohttp.web_exceptions import HTTPBadRequest
from aiohttp_jinja2 import render_template
from multidict import MultiDict, MultiDictProxy

from bigur.auth.utils import asdict, parse_accept, choice_content_type

from bigur.auth.authn.user.base import AuthN

logger = getLogger(__name__)

FIELD_LEN_LIMIT = 1024


class Registration(AuthN):
    '''User registration class.'''

    async def get(self) -> Response:
        request = self.request
        context = {
            'endpoint':
                request.app['config'].get(
                    'http_server.endpoints.registration.path'),
            'query':
                request.query,
            'prefix':
                request.app['config'].get('http_server.static.prefix', '/')
        }
        logger.debug('Context: %s', context)
        return render_template('registration_form.j2', request, context)

    async def post(self) -> Response:
        request = self.request
        ctype = request.headers.get('content-type')

        logger.debug('Request Content-Type: %s', ctype)

        form: MultiDictProxy

        if ctype == 'application/json':
            try:
                data: Any = await request.json()
                if not isinstance(data, dict):
                    raise ValueError('Invalid request type')
            except ValueError as e:
                logger.warning('Invalid request: %s', e)
                raise HTTPBadRequest(reason='Invalid request') from e
            else:
                form = MultiDictProxy(MultiDict(cast(Dict, data)))

        elif ctype == 'application/x-www-form-urlencoded':
            form = await self.request.post()

        else:
            raise HTTPBadRequest(reason='Invalid content type')

        logger.debug('Form is: %s', form)

        user = await self.request.app['store'].users.create(
            **{
                'username': form.get('username'),
                'password': form.get('password'),
                'given_name': form.get('given_name'),
                'patronymic': form.get('patronymic'),
                'family_name': form.get('family_name')
            })
        await self.request.app['store'].users.put(user)

        if 'next' in form:
            response = Response(
                status=303,
                reason='See Other',
                charset='utf-8',
                headers={
                    'Location':
                        '{}?{}'.format(
                            form.get('next'),
                            urlencode({
                                'state': form.get('state')
                            }, doseq=True))
                })
        else:
            accepts = parse_accept(request.headers.get('Accept'))
            ctype = choice_content_type(accepts,
                                        ['application/json', 'text/plain'])
            logger.debug('Content-type for response is: %s', ctype)

            if ctype == 'application/json':
                user_dict = asdict(user)
                user_dict.pop('crypt')
                user_dict.pop('salt')
                response = json_response({
                    'meta': {
                        'status': 'ok'
                    },
                    'data': user_dict
                })

            else:
                response = Response(text='Login successful')

        self.set_cookie(self.request, response, user.get_id())

        return response
