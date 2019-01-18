__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import View
from aiohttp_jinja2 import render_template
from oauthlib.common import Request


class OwnerPasswordHandler(View):
    async def get_oauth_request(self):
        body = await self.request.text()
        return Request(
            self.request.path,
            self.request.method,
            body,
            self.request.headers
        )

    async def post(self):
        server = self.request.app['server']
        request = await self.get_oauth_request()
        body = await self.request.text()
        headers, body, status = server.create_token_response(
            self.request.path,
            self.request.method,
            body,
            self.request.headers
        )
        print(headers, body, status)
        context = {}
        response = render_template('login_form.html', self.request, context)
        return response
