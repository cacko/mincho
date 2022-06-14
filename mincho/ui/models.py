from re import U
from sys import prefix
from rumps import MenuItem
from pathlib import Path
from enum import Enum
from dataclasses_json import dataclass_json, Undefined
from dataclasses import dataclass
from typing import Optional
import arrow
from mincho.core.string import name_to_code


class Label(Enum):
    START = 'Start'
    STOP = 'Stop'
    DEFAULT = 'Default'
    CPUPLUS = 'CPU+'
    MAX = 'Max'
    QUIT = 'Quit'


class Icon(Enum):
    ON = 'on.png'
    OFF = 'off.png'
    DEFAULT = 'default.png'
    CPUPLUS = 'cpuplus.png'
    MAX = 'max.png'
    QUIT = 'quit.png'
    WALLET = 'wallet.png'
    LAST_SEEN = 'last_seen.png'
    WORKER = 'worker.png'
    POWERPLUG = 'powerplug.png'
    USD = 'usd.png'
    ESCAPE = 'escape.png'
    PROBE = 'probe.png'
    POWER = 'power.png'
    POWEROFF = 'poweroff.png'
    THREADS = "threads.png"

    def __new__(cls, *args):
        icons_path: Path = Path(__file__).parent / "icons"
        value = icons_path / args[0]
        obj = object.__new__(cls)
        obj._value_ = value.as_posix()
        return obj


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ApiStats:
    activeWorkers: int
    lastSeen: int
    usdPerMin: float
    averageHashrate: float
    currentHashrate: float
    pool: str


class ActionItemMeta(type):

    _instances = {}

    def __call__(cls, name, *args, **kwds):
        if name not in cls._instances:
            cls._instances[name] = super().__call__(*args, **kwds)
        return cls._instances[name]

    @property
    def start(cls) -> 'ActionItem':
        return cls("start", Label.START.value, icon=Icon.POWER.value)

    @property
    def stop(cls) -> 'ActionItem':
        return cls("stop", Label.STOP.value, icon=Icon.POWEROFF.value)

    @property
    def default(cls) -> 'ActionItem':
        return cls("default", Label.DEFAULT.value, icon=Icon.DEFAULT.value)

    @property
    def cpuplus(cls) -> 'ActionItem':
        return cls("cpuplsu", Label.CPUPLUS.value, icon=Icon.CPUPLUS.value)

    @property
    def max(cls) -> 'ActionItem':
        return cls("maxx", Label.MAX.value, icon=Icon.MAX.value)

    @property
    def usd_per_minute(cls) -> 'StatItem':
        return cls("usd_per_minute", "-", icon=Icon.USD.value)

    @property
    def last_seen(cls) -> 'StatItem':
        return cls("last_seen", "-", icon=Icon.LAST_SEEN.value)

    @property
    def active_workers(cls) -> 'StatItem':
        return cls("active_worker", "-", prefix="Workers", icon=Icon.WORKER.value)

    @property
    def current_hashrate(cls) -> 'StatItem':
        return cls("current_hashrate", "-", icon=Icon.POWERPLUG.value)

    @property
    def threads(cls) -> 'StatItem':
        return cls("threads", "-", prefix="Threads", icon=Icon.THREADS.value)

    @property
    def quit(cls) -> 'ActionItem':
        return cls("quit", Label.QUIT.value, icon=Icon.QUIT.value)


class ActionItem(MenuItem, metaclass=ActionItemMeta):
    pass


class ToggleAction(ActionItem):
    _states = ['hide', 'show']

    def toggle(self, state: bool):
        getattr(self, self._states[int(state)])()


class StatItem(ActionItem):

    prefix: str = None

    def __init__(self, title, prefix: str = None, **kwargs):
        self.prefix = prefix
        super().__init__(title, **kwargs)

    def number(self, value=None):
        if prefix:
            self.title = f"{self.prefix}: {value}"
        else:
            self.template = f"{value}"
        self.set_callback(lambda x: True)

    def relative_time(self, value=None):
        self.title = arrow.get(value).humanize(arrow.utcnow())
        self.set_callback(lambda x: True)

    def money(self, value=None):
        self.title = F"{float(value):.5f}$"
        self.set_callback(lambda x: True)

    def hashrate(self, value=None):
        value = value / 1000000
        self.title = f"{value:.3f} MH/s"
        self.set_callback(lambda x: True)


class Preset(Enum):
    DEFAULT = "default"
    CPUPLUS = "cpuplus"
    MAXX = "max"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class BarStats:
    local_hr: Optional[float] = None
    preset: Optional[str] = "default"
    remote_hr: Optional[float] = None

    @property
    def display(self):
        parts = filter(None, [
            f"{name_to_code(self.preset).upper()}",
            f"{self.local_hr:.2f}MH/s" if self.local_hr else None,
            f"{self.remote_hr:.2f}MH/s" if self.remote_hr else None,
        ])
        return " | ".join(parts)
