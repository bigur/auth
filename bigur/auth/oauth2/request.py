__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass

from aiohttp.web import Request

from bigur.auth.model import User


@dataclass
class OAuth2Request:
    owner: User

async def create_request(cls: Type, request: Request) -> Request:
    if request.method == 'GET':
        params = request.query
    elif request.method == 'POST':
        params = await request.post()
    else:
        ValueError('Unsupported method %s', request.method)

    try:
        kwargs = {
            key: params[key]
            for key in cls.__dataclass_fields__
            if key in params
        }
        request['oauth2_request'] = cls(**kwargs)

    except TypeError as e:
        msg = str(e)[11:].capitalize().replace(' positional', '')
        raise ParameterRequired(msg, request=request)

    else:
        return request
