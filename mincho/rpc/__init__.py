import re
from typing import Optional
from jsonrpcclient import request_json
import asyncio
from asyncio import StreamReader, StreamWriter
from queue import Queue
from mincho import log
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined
from enum import Enum


class Method(Enum):
    STATUS = "status"
    HELLO = "hello"
    EXIT = "exit"
    SHUTDOWN = "shutdown"
    CONNECT = "connect"
    HASHRATE = "hashrate"
    START = "start"
    STOP = "stop"
    THREADS = "threads"
    hashes = "hashes"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Request:
    method: Method
    params: Optional[list] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Response:
    error: Optional[str] = None
    id: Optional[str] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class StatusResult:
    devfee_connected: bool
    hashes: int
    hashrate: int
    mode: str
    threads_current: int
    upstream_connected: dict[str, bool]

    @property
    def connected(self):
        if not self.upstream_connected:
            return False
        return any([v for v in self.upstream_connected.values()])


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Status(Response):
    result: list[StatusResult] = None


class Client:
    eventLoop: asyncio.AbstractEventLoop = None
    __rstream: StreamReader = None
    __wstream: StreamWriter = None
    input: Queue = None
    __connected: bool = False

    def __init__(self, app) -> None:
        self.eventLoop = asyncio.new_event_loop()
        self.input = Queue()
        self.app = app

    def start(self):
        self.eventLoop.create_task(self.miner_processor())
        self.eventLoop.run_forever()

    async def connect(self, reconnect=False):
        try:
            if not self.__connected:
                self.__rstream, self.__wstream = await asyncio.open_connection(
                    '127.0.0.1', 3326)
                self.__connected = True
                log.debug(f"connected {self.__rstream}")
        except Exception:
            print("recoonect fail")

    async def miner_processor(self):
        while True:
            await self.connect()
            await self.commander()

    async def commander(self) -> Status:
        try:
            req: Request = self.input.get()
            payload = request_json(
                method=req.method.value,
                params=req.params
            ) + "\n"
            log.debug(payload)
            self.__wstream.write(payload.encode())
            await self.__wstream.drain()
            msg = await self.__rstream.readline()
            log.debug(msg)
            self.input.task_done()
            self.app.onResult(req.method, msg)
        except:
            self.__connected = False
            self.app.status_icon(False)
