__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from urllib.parse import urlparse

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.exceptions import InvalidRedirectionURI

logger = getLogger(__name__)


async def validate_redirect_uri(context: Context) -> Context:
    client = context.client
    redirect_uri = context.oauth2_request.redirect_uri

    if not redirect_uri:
        raise InvalidRedirectionURI('Missing `redirect_uri\' parameter.')

    if not urlparse(redirect_uri).netloc:
        raise InvalidRedirectionURI(
            'Not absolute path in `redirect_uri\' parameter.')

    if not client:  # It can't happen
        raise InvalidRedirectionURI('Can\'t verify `redirect_uri\' parameter.')

    if not client.redirect_uris or redirect_uri not in client.redirect_uris:
        raise InvalidRedirectionURI(
            'This `redirect_uri\' value is not allowed.')

    return context
