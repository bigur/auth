__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from urllib.parse import urlencode

from aiohttp.web import Response
from aiohttp_jinja2 import render_template

from .base import AuthN


class Registration(AuthN):

    async def get(self):
        context = {
            'endpoint':
                self.request.app['config'].get(
                    'http_server.endpoints.registration.path'),
            'query':
                self.request.query,
        }
        return render_template('registration_form.j2', self.request, context)

    async def post(self):
        # TODO: validate and strip
        form = await self.request.post()
        user = await self.request.app['store'].users.create(
            **{
                'username': form.get('username'),
                'password': form.get('password'),
                'given_name': form.get('given_name'),
                'patronymic': form.get('patronymic'),
                'family_name': form.get('family_name')
            })
        await self.request.app['store'].users.put(user)

        if 'next' not in form:
            response = Response(text='Login successful')

        else:
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

        self.set_cookie(self.request, response, user.get_id())

        return response
