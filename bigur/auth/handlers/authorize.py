__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import View
from aiohttp_jinja2 import render_template


class AuthorizeHandler(View):
    async def get(self):
        context = {}
        response = render_template('login_form.html', self.request, context)
        return response
