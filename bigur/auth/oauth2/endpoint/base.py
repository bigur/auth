__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from typing import Optional

from bigur.rx import ObservableBase, ObserverBase, Subject

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response


class Endpoint(ObservableBase, ObserverBase):

    def __init__(self, request: OAuth2Request):
        self._request = request
        self._observer: Optional[ObserverBase] = None

    async def _subscribe(self, observer: ObserverBase):
        self._observer = observer

        stream = Subject()

        await self._chain(stream).subscribe(self)

        try:
            await stream.on_next(self._request)
        except Exception as error:
            await self._observer.on_error(error)
        else:
            await stream.on_completed()

    def _chain(self, stream: ObservableBase) -> ObservableBase:
        raise NotImplementedError

    async def on_next(self, response: OAuth2Response):
        if self._observer is not None:
            await self._observer.on_next(response)

    async def on_error(self, error: Exception):
        if self._observer is not None:
            await self._observer.on_error(error)

    async def on_completed(self):
        if self._observer is not None:
            await self._observer.on_completed()
