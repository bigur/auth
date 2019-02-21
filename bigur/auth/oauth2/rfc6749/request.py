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


async def create_request(cls: Type, http_request: Request) -> Request:
    if http_request.method == 'GET':
        params = http_request.query
    elif http_request.method == 'POST':
        params = await http_request.post()
    else:
        ValueError('Unsupported method %s', http_request.method)

    try:
        kwargs = {
            key: params[key]
            for key in cls.__dataclass_fields__
            if key in params
        }
        http_request['oauth2_request'] = cls(**kwargs)

    except TypeError as e:
        msg = str(e)[11:].capitalize().replace(' positional', '')
        raise ParameterRequired(msg, http_request=http_request)

    else:
        return http_request
