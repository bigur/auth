__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from typing import List, TypeVar

from bigur.rx import Subject, Observer, operators as op

from bigur.auth.oauth2.rfc6749.validators import validate_client_id


logger = getLogger('bigur.auth.oauth2.rfc6749.endpoint.authorization')


T_in = TypeVar('T_in')
T_out = TypeVar('T_out')


class AuthorizationEndpoint(Subject):
    def __init__(self)
