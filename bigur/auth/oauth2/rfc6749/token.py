__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'


class Token:
    pass


class BearerToken(Token):
    pass


class JWTBearerToken(BearerToken):
    pass
