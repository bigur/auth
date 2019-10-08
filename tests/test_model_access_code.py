__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from datetime import datetime

from pytest import mark


class TestAccessCode(object):
    '''Test access codes.'''

    @mark.asyncio
    async def test_create(self, store):
        code = await store.access_codes.create()
        assert isinstance(code.created, datetime)
        assert code.code
        assert not code.used
