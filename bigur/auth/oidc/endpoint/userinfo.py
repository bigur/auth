__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass

from rx import Observable, just
from rx import operators as op

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response


@dataclass
class UserInfoRequest(OAuth2Request):
    owner: str


@dataclass
class UserInfoResponse(OAuth2Response):
    sub: str


def get_user_info_stream(request: UserInfoRequest) -> Observable:
    pass


"""
def user_info(request: UserInfoRequest) -> UserInfoResponse:
    return UserInfoResponse(sub=request.owner)


class UserInfoEndpoint(Endpoint):

    def _chain(self, stream: ObservableType) -> ObservableType:
        return (stream | op.map(user_info))
 """
