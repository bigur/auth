__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Response, View


class RootHandler(View):
    async def get(self):
        return Response(text='/')
