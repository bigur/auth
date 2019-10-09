__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass


@dataclass
class BaseResponse:
    pass


@dataclass
class OAuth2Response(BaseResponse):
    pass
