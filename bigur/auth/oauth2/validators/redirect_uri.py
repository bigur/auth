__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.auth.oauth2.exceptions import InvalidRedirectionURI
from bigur.auth.oauth2.request import OAuth2Request

logger = getLogger(__name__)


async def validate_redirect_uri(request: OAuth2Request) -> OAuth2Request:
    logger.warning('Validate redirect_uri stub')
    redirect_uri = request.redirect_uri

    # XXX: redirect_uri is optional, if it not defined we must take it
    # from client.
    if not redirect_uri:
        raise InvalidRedirectionURI('Missing \'redirect_uri\' parameter')

    return request
