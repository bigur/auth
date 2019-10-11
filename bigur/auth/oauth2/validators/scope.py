__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.store import store
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.exceptions import InvalidScope


async def validate_scope(context: Context) -> Context:
    codes = context.oauth2_request.scope
    if not codes:
        default_scopes = await store.scopes.get_default_scopes()
        if not default_scopes:
            raise InvalidScope('No scope in request and '
                               'no default scopes configured.')
        else:
            context.oauth2_request.scope = {x.code for x in default_scopes}
    else:
        scopes = []
        for code in codes:
            try:
                scopes.append(await store.scopes.get_by_code(code))
            except KeyError as e:
                raise InvalidScope('Invalid scope `{}\'.'.format(code)) from e

    return context
