__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2018 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger
from json import dumps, loads, JSONEncoder
from re import sub
from time import time

from aio_pika import Message
from aio_pika import connect_robust

from bigur.utils import config, AttrDict


logger = getLogger('bigur.auth.amqp.core')


class Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, AttrDict):
            return obj.__dict__
        return JSONEncoder.default(self, obj)


class Connection(object):
    def __new__(cls, *args, **kwargs):
        if not getattr(cls, '__instance', None):
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

    def __init__(self):
        self._connection = None
        self._channel = None

    async def get_connection(self):
        if self._connection is None:
            self._connection = await connect_robust(config.get('auth', 'url'))
        return self._connection

    async def get_channel(self):
        if self._channel is None:
            connection = await self.get_connection()
            self._channel = await connection.channel()
        return self._channel


class Service(object):

    __section__ = 'gql'

    def __init__(self):
        self._connection = Connection()

    async def consume(self):
        channel = await self._connection.get_channel()

        queue_name = '{}.{}'.format(self.__section__,
            sub(r'([A-Z])', r'_\1', type(self).__name__)[1:].lower())

        queue = await channel.declare_queue(queue_name)

        await queue.consume(self.on_get_message)

    async def on_get_message(self, message):
        queue_name = '{}.{}'.format(self.__section__,
            sub(r'([A-Z])', r'_\1', type(self).__name__)[1:].lower())
        logger.debug('Получен запрос в очереди %s', queue_name)
        try:
            payload = loads(message.body)
            result = await self.call(
                context=payload['context'],
                **payload['kwargs']
            )
            message_type = 'result'
        except Exception as e:
            logger.error('Ошибка при выполнении запроса:', exc_info=e)
            message_type = 'error'
            result = {'error': '{}: {}'.format(type(e).__name__, e)}

        encoded = dumps(result, ensure_ascii=False, cls=Encoder)
        from pprint import pprint
        pprint(encoded)
        result_message = Message(
            dumps(result, ensure_ascii=False, cls=Encoder).encode(),
            delivery_mode=message.delivery_mode,
            correlation_id=message.correlation_id,
            timestamp=time(),
            type=message_type)
        channel = await self._connection.get_channel()
        await channel.default_exchange.publish(result_message,
                                               message.reply_to,
                                               mandatory=False)
        message.ack()

    async def call(self, *args, **kwargs):
        raise NotImplementedError('метод должен быть перекрыт')

