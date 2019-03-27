__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from typing import Type

from multidict import MultiDictProxy

from bigur.auth.model import User
from bigur.auth.oauth2.exceptions import ParameterRequired


@dataclass
class OAuth2Request:
    owner: User


async def create_request(cls: Type, owner: User, params: MultiDictProxy) -> OAuth2Request:
    try:
        kwargs = {
            key: params[key]
            for key in cls.__dataclass_fields__
            if key in params
        }
        kwargs['owner'] = owner
        request = cls(**kwargs)

    except TypeError as e:
        message = str(e)[11:].capitalize().replace(' positional', '')
        raise ParameterRequired(message)

    else:
        return request
