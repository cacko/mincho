from unittest.mock import patch
import rumps
from rumps import MenuItem
from threading import Thread
from queue import Queue
from mincho.rpc import (
    Client,
    Method,
    Request,
    Status
)
from mincho import log
from pathlib import Path
from enum import Enum
from os import environ


class Icon(Enum):
    ON = 'on.png'
    OFF = 'off.png'


class Action(Enum):
    START = 'Start'
    STOP = 'Stop'
    DEFAULT = 'Default'
    CPUPLUS = 'CPU+'
    MAX = 'Max'


class Config(Enum):
    DEFAULT = "default"
    CPUPLUS = "cpuplus"
    MAX = "max"


class MinchoApp(rumps.App):

    queue: Queue = None
    __connected: bool = False
    __icons_cache: dict[Icon, str] = {}
    __config_path: Path = None
    __active_config: Config = None

    def __init__(self):
        super(MinchoApp, self).__init__(
            name="Mincho",
            menu=[
                MenuItem("Start"),
                MenuItem("Stop"),
                None,
                MenuItem("Default"),
                MenuItem("CPU+"),
                MenuItem("Max"),
                None,
            ]
        )
        self.__config_path = Path(environ.get("MINCHO_CONFIG", "."))
        self.icon = self.get_icon(Icon.OFF)
        self.menu_item(Action.START).hide()
        rpc = Client(self)
        self.queue = rpc.input
        t = Thread(target=rpc.start)
        t.start()

    def get_icon(self, icon: Icon):
        if icon not in self.__icons_cache:
            path = Path(__file__).parent / "icons" / icon.value
            self.__icons_cache[icon] = path.as_posix()
        return self.__icons_cache.get(icon)

    def menu_item(self, action: Action) -> MenuItem:
        return self.menu.get(action.value)

    @property
    def active_config(self) -> Config:
        if not self.__config_path.exists():
            return None
        cfp = self.__config_path.resolve().name
        try:
            return Config(cfp)
        except ValueError:
            return None

    def change_config(self, cfg: Config):
        self.menu_item(
            Action[self.active_config.value.upper()]).state = 0
        parent = self.__config_path.parent
        new_config: Path = parent / cfg.value
        self.__config_path.unlink()
        self.__config_path.symlink_to(new_config)

    @rumps.clicked("Default")
    def onDefault(self, sender):
        self.change_config(Config.DEFAULT)
        self.queue.put_nowait(Request(method=Method.SHUTDOWN))

    @rumps.clicked("CPU+")
    def onCpu(self, sender):
        self.change_config(Config.CPUPLUS)
        self.queue.put_nowait(Request(method=Method.SHUTDOWN))

    @rumps.clicked("Max")
    def onMax(self, sender):
        self.change_config(Config.MAX)
        self.queue.put_nowait(Request(method=Method.SHUTDOWN))

    @rumps.clicked("Stop")
    def onStart(self, sender):
        self.queue.put_nowait(Request(
            method=Method.STOP,
        ))

    @rumps.clicked("Start")
    def onStop(self, sender):
        self.queue.put_nowait(Request(
            method=Method.START,
        ))

    @rumps.timer(5)
    def updateStatus(self, sender):
        self.queue.put_nowait(
            Request(method=Method.STATUS)
        )

    def onResult(self, method: Method, res: str):
        match(method):
            case Method.STATUS:
                return self.on_status(Status.from_json(res))

    def status_icon(self, status: bool):
        if status != self.__connected:
            self.__connected = status
            icon = Icon.ON if status else Icon.OFF
            self.icon = self.get_icon(icon)
            getattr(self.menu_item(Action.START),
                    'hide' if self.__connected else 'show')()
            getattr(self.menu_item(Action.STOP),
                    'show' if self.__connected else 'hide')()
            if self.__connected:
                try:
                    self.menu_item(
                        Action[self.active_config.value.upper()]).state = 1
                except Exception as e:
                    print(e)

    def on_status(self, res: Status):
        log.debug(res)
        self.status_icon(res.result[0].connected)
        hash_rate = [f"{r.hashrate / 100000:.2f}" for r in res.result]
        threads = [f"{r.threads_current}" for r in res.result]
        self.title = f"HR: {' '.join(hash_rate)} | TH: {' '.join(threads)}"
