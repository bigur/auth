__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp_cors import CorsViewMixin, ResourceOptions, custom_cors

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oidc.endpoint.userinfo import UserInfoEndpoint, UserInfoRequest

logger = getLogger(__name__)


class UserInfoHandler(OAuth2Handler, CorsViewMixin):

    __endpoint__ = UserInfoEndpoint
    __request_class__ = UserInfoRequest

    @custom_cors(
        {'*': ResourceOptions(allow_credentials=True, allow_headers='*')})
    async def get(self):
        return await super().get()
