__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict, dataclass
from functools import partial
from logging import getLogger
from typing import Any, Dict

from bigur.rx import ObservableType, ObserverType, Subject
from bigur.rx import operators as op

# yapf: disable
from bigur.auth.oauth2.grant import (
    authorization_code_grant as oauth2_authorization_code_grant,
    implicit_grant as oauth2_implicit_grant)
# yapf: enable
from bigur.auth.oauth2.grant.implicit import OAuth2TokenResponse
from bigur.auth.oauth2.endpoint.base import Endpoint
from bigur.auth.oauth2.validators import (validate_client_id,
                                          authenticate_client,
                                          validate_redirect_uri)
from bigur.auth.oidc.grant import implicit_grant
from bigur.auth.oidc.grant.implicit import IDTokenResponse
from bigur.auth.oidc.request import OIDCRequest
from bigur.auth.oidc.validators import (validate_response_type, validate_scope)

logger = getLogger(__name__)


@dataclass
class AuthorizationResponse(IDTokenResponse, OAuth2TokenResponse):
    pass


# Where is no join operator in bigur.rx
def iter_response_types():

    class IterResponseTypes(Subject):

        def __init__(self, source):
            self._source = source
            self._subscription = None
            super().__init__()

        async def _subscribe(self, observer: ObserverType):
            await super()._subscribe(observer)
            if self._subscription is None:
                self._subscription = await self._source.subscribe(self)

        async def _unsubscribe(self, observer: ObserverType):
            await super().unsubscribe(observer)
            if not len(self._observers) and self._subscription is not None:
                await self._subscription.unsubscribe()
                self._subscription = None

        async def on_next(self, request: OIDCRequest):
            if not self.is_stopped:
                for response_type in sorted(
                        request.response_type,
                        key=lambda x: x == 'id_token' and 1 or 0):
                    await super().on_next((response_type, request))

    def iter_base(source: ObservableType):
        return IterResponseTypes(source)

    return partial(iter_base)


def merge_responses():

    class MergeResponsesSubject(Subject):

        def __init__(self, source: ObservableType):
            self._source = source
            self._subscription = None
            self._params: Dict[str, Any] = {}
            super().__init__()

        async def _subscribe(self, observer: ObserverType):
            await super()._subscribe(observer)
            if self._subscription is None:
                self._subscription = await self._source.subscribe(self)

        async def _unsubscribe(self, observer: ObserverType):
            await super().unsubscribe(observer)
            if not len(self._observers) and self._subscription is not None:
                await self._subscription.unsubscribe()
                self._subscription = None

        async def on_next(self, response):
            logger.debug('MergeResponsesSubject on_next: %s', response)
            self._params.update(asdict(response))

        async def on_completed(self):
            response = AuthorizationResponse(**self._params)
            for observer in self._observers:
                await observer.on_next(response)
                await observer.on_completed()

    def merge(source: ObservableType):
        return MergeResponsesSubject(source)

    return partial(merge)


class AuthorizationEndpoint(Endpoint):

    def _chain(self, stream: ObservableType) -> ObservableType:

        base_branch = (
            stream
            | op.map(validate_client_id)
            | op.map(authenticate_client)
            | op.map(validate_redirect_uri)
            | op.map(validate_response_type)
            | op.map(validate_scope)
            | iter_response_types())

        oauth2_implicit_branch = (
            base_branch
            | op.filter(lambda x: x[0] == 'code')
            | op.map(lambda x: x[1])
            | op.map(oauth2_authorization_code_grant))

        oauth2_authorization_code_branch = (
            base_branch
            | op.filter(lambda x: x[0] == 'token')
            | op.map(lambda x: x[1])
            | op.map(oauth2_implicit_grant))

        oidc_implicit_branch = (
            base_branch
            | op.filter(lambda x: x[0] == 'id_token')
            | op.map(lambda x: x[1])
            | op.map(implicit_grant))

        merge_branch = (
            op.concat(oauth2_implicit_branch, oauth2_authorization_code_branch,
                      oidc_implicit_branch)
            | merge_responses())

        return merge_branch
