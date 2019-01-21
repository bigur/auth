__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Response, View

from bigur.rx import Subject
from bigur.rx import operators as op

from bigur.auth.oauth2.rfc6749.validators import validate_client_id


class AuthorizationHandler(View):

    async def post(self):
        stream = (
            Subject()
            | op.map(validate_client_id)
        )

        response = Response()

        async def on_sucess(value):
            response.text = 'ok!'

        async def on_error(error):
            response.text = 'error!'

        async def on_completed():
            pass

        await x.subscribe(on_sucess, on_error)

        await x.on_next(self.request)

        return response
