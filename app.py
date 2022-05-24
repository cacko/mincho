from jsonrpcclient import request_json
import rumps
import asyncio
from asyncio import Queue, StreamReader, StreamWriter
from threading import Thread
import logging
from os import environ

logging.basicConfig(
    level=getattr(logging, environ.get("MINCHO_LOG_LEVEL", "DEBUG")),
    format="%(filename)s %(message)s",
    datefmt="MINCH %H:%M:%S",
)
log = logging.getLogger("BOTYO")


class RPCMeta(type):
    _instance: 'RPC' = None
    _host: str = '127.0.0.1'
    _post: int = 3326

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = type.__call__(cls, *args, **kwargs)
        return cls._instance

    def serve(cls):
        cls().doStart()

    @property
    def output(cls):
        return cls()._output

    @property
    def input(cls):
        return cls()._input


class RPC(object, metaclass=RPCMeta):
    eventLoop: asyncio.AbstractEventLoop = None
    _output: asyncio.Queue = None
    _input: asyncio.Queue = None
    _rstream: StreamReader = None
    _wstream: StreamWriter = None
    _registered: bool = False

    def doStart(self):
        self.eventLoop = asyncio.new_event_loop()
        self._output = asyncio.Queue()
        self._input = asyncio.Queue()
        self.eventLoop.create_task(self._produce_consume_messages())
        self.eventLoop.run_forever()

    async def connect(self, reconnect=False):
        try:
            if reconnect:
                await asyncio.sleep(5)
            self._rstream, self._wstream = await asyncio.open_connection(
                '127.0.0.1', 3326)
            print(self._rstream, self._wstream)
            await self._output.put("hello")
        except Exception:
            print("recoonect fail")

    async def _produce_consume_messages(self, consumers=3):
        readers = [
            asyncio.create_task(self._reader(1)),
        ]
        writers = [
            asyncio.create_task(self._consume(n))
            for n in range(1, consumers + 1)
        ]
        await asyncio.gather(*readers)
        await self._output.join()
        for c in writers:
            c.cancel()

    async def _reader(self, name: int) -> None:
        try:
            await self.connect()
            while True:
                try:
                    msg = await self._rstream.readline()
                    await self._input.put(msg)
                except Exception as e:
                    print(e)
        except Exception as e:
            raise Exception(f"Cannot receive messages: {e}")

    async def _consume(self, name: int) -> None:
        while True:
            try:
                await self._consume_new_item(name)
            except Exception:
                continue

    async def _consume_new_item(self, msg: str) -> None:
        msg = await self._output.get()

        self._wstream.write(f"{request_json(msg)}\n".encode())
        await self._wstream.drain()
        self._output.task_done()


class StockApp(rumps.App):

    queue: Queue = None

    def __init__(self):
        super(StockApp, self).__init__(name="Stock")
        self.stock = "AAPL"
        self.icon = "icon.png"

    @ rumps.clicked("Search...")
    @ rumps.clicked("MSFT")
    @ rumps.clicked("TSLA")
    @ rumps.clicked("NFLX")
    @ rumps.clicked("FB")
    @ rumps.clicked("AAPL")
    def changeStock(self, sender):
        if sender.title != "Search...":
            self.title = f" 🔍 {sender.title}"
            self.stock = sender.title
        else:
            window = rumps.Window(
                f"Current: {self.stock}", "Search another stock")
            window.icon = self.icon
            response = window.run()
            self.stock = response.text

    @rumps.timer(5)
    def updateStockPrice(self, sender):
        if not self.queue:
            thread = Thread(target=RPC.serve())
            thread.start()
            self.queue = RPC.output
        self.queue.put("status")

    async def getStock(self, msg="status"):
        print("Test")


if __name__ == '__main__':
    StockApp().run()
