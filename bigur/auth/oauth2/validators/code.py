__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from datetime import datetime, timedelta

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.exceptions import InvalidRequest, InvalidGrant
from bigur.auth.store import store

EXPIRE_SECONDS = 60 * 10


async def validate_code(context: Context) -> Context:
    code = context.oauth2_request.code
    if not code:
        raise InvalidRequest('Parameter `code\' required.')

    try:
        access_code = await store.access_codes.get_by_code(code)
    except KeyError as e:
        raise InvalidGrant('Invalid code provided.') from e

    if access_code.created + timedelta(seconds=EXPIRE_SECONDS) < datetime.now():
        raise InvalidGrant('Code expired.')

    return context
