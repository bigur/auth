__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import View, json_response
from aiohttp_cors import CorsViewMixin, ResourceOptions, custom_cors

logger = getLogger(__name__)


class UserInfoHandler(View, CorsViewMixin):

    @custom_cors({'*': ResourceOptions()})
    async def get(self):
        logger.warning('UserInfo endpoint stub')
        return json_response({})
