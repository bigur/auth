__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request
from multidict import MultiDict

logger = getLogger(__name__)


async def authenticate_client(request: Request, params: MultiDict) -> None:
    '''This method do client authentication. If it finished sucessfull
    method return nothing, overwise raises http error.

    :returns: None
    :throw: :class:`~aiohttp.web.HTTPException`'''
    logger.warning('Client authentication stub')
