__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import View
from aiohttp_jinja2 import template


class LoginFormHandler(View):

    @template('login_form.html')
    async def get(self):
        return {}
