
from queue import Queue
from cachable.request import Request
from asyncio import AbstractEventLoop, new_event_loop
from mincho import app_config
from mincho.api.models import CurrentStats, Method


class ClientMeta(type):
    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance


class Client(object, metaclass=ClientMeta):

    input: Queue = None
    __callback: callable = None
    eventLoop: AbstractEventLoop = None

    def __init__(self, callback: callable) -> None:
        self.eventLoop = new_event_loop()
        self.input = Queue()
        self.__callback = callback

    def start(self):
        self.eventLoop.create_task(self.api_processor())
        self.eventLoop.run_forever()

    async def api_processor(self):
        while True:
            method = self.input.get()
            result = await Request(method.value.replace("<client_id>", app_config.client_id)).json
            match(method):
                case Method.STATS:
                    self.__callback(CurrentStats.from_dict(result))
