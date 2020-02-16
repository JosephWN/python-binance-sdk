import asyncio

from binance.common.exceptions import \
    InvalidSubParamsException, InvalidSubTypeParamException
from binance.common.utils import normalize_symbol
from binance.common.constants import ATOM, KEY_PAYLOAD, KEY_PAYLOAD_TYPE

class ProcessorBase(object):
    # The handler class
    HANDLER = None

    # The payload['e'] of message
    PAYLOAD_TYPE = ATOM

    # subtype used by client.subscribe
    SUB_TYPE = None

    def __init__(self, client):
        self._client = client

        self._handlers = set()
        self.PAYLOAD_TYPE = self.PAYLOAD_TYPE \
            if self.PAYLOAD_TYPE != ATOM else self.SUB_TYPE

    def subscribe_param(self, subscribe, t, *args):
        if len(args) == 0:
            raise InvalidSubTypeParamException(
                t, 'symbol', 'string expected but not specified')

        symbol = args[0]

        if type(symbol) is not str:
            raise InvalidSubTypeParamException(
                t, 'symbol', 'string expected but got `%s`' % symbol)

        return normalize_symbol(symbol) + '@' + t

    def is_handler_type(self, handler):
        return isinstance(handler, self.HANDLER)

    def is_message_type(self, msg):
        payload = msg.get(KEY_PAYLOAD)

        if payload != None and \
            getattr(payload, KEY_PAYLOAD_TYPE, None) == self.PAYLOAD_TYPE:
            return True, payload

        return False, None

    def is_subtype(self, t):
        return t == self.SUB_TYPE

    def add_handler(self, handler):
        self._handlers.add(handler)

        # set the client to handler
        handler._client = self._client

    async def dispatch(self, payload):
        coro = []

        for handler in self._handlers:
            if asyncio.iscoroutinefunction(handler.receive):
                coro.append(handler.receive(payload))
            else:
                handler.receive(payload)

        if len(coro) > 0:
            await asyncio.gather(*coro)
