__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict, dataclass
from logging import getLogger
from typing import Type

from aiohttp.web import Request

from bigur.auth.oauth2.rfc6749.errors import ParameterRequired

logger = getLogger(__name__)


@dataclass
class OAuth2Request:

    def asdict(self, *, dict_factory=dict):
        result = dict_factory()
        for k, v in asdict(self).items():
            if v is None:
                continue
            if isinstance(v, list) and not v:
                continue
            result[k] = v
        return result


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
