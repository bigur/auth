__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import mark

from bigur.auth.model import Scope


class TestScope(object):
    '''Test scopes.'''

    @mark.asyncio
    async def test_create(self):
        Scope(code='openid', title='OpenID Connect requests', default=False)
