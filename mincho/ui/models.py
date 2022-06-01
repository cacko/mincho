from rumps import MenuItem
from pathlib import Path
from enum import Enum
from dataclasses_json import dataclass_json, Undefined
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import arrow


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
    def __new__(cls, *args):
        icons_path: Path = Path(__file__).parent / "icons"
        value = icons_path / args[0]
        obj = object.__new__(cls)
        obj._value_ = value.as_posix()
        return obj


class ActionItemMeta(type):

    _instances = {}

    def __call__(cls, name, *args, **kwds):
        if name not in cls._instances:
            cls._instances[name] = super().__call__(*args, **kwds)
        return cls._instances[name]

    @property
    def start(cls) -> 'ActionItem':
        return cls("start", "Start", icon=Icon.POWER.value)

    @property
    def stop(cls) -> 'ActionItem':
        return cls("stop", "Stop", icon=Icon.POWEROFF.value)

    @property
    def default(cls) -> 'ActionItem':
        return cls("default", "Default", icon=Icon.DEFAULT.value)

    @property
    def cpuplus(cls) -> 'ActionItem':
        return cls("cpuplsu", "CPU+", icon=Icon.CPUPLUS.value)

    @property
    def max(cls) -> 'ActionItem':
        return cls("maxx", "Max", icon=Icon.MAX.value)

    @property
    def usd_per_minute(cls) -> 'StatItem':
        return cls("usd_per_minute", "-", icon=Icon.USD.value)

    @property
    def last_seen(cls) -> 'StatItem':
        return cls("last_seen", "-", icon=Icon.LAST_SEEN.value)

    @property
    def active_workers(cls) -> 'StatItem':
        return cls("active_worker", "-", icon=Icon.WORKER.value)

    @property
    def current_hashrate(cls) -> 'StatItem':
        return cls("current_hashrate", "-", icon=Icon.POWERPLUG.value)


class ActionItem(MenuItem, metaclass=ActionItemMeta):
    pass


class ToggleAction(ActionItem):
    _states = ['hide', 'show']

    def toggle(self, state: bool):
        getattr(self, self._states[int(state)])()


class StatItem(ActionItem):

    def number(self, value=None):
        self.title = f"Workers: {value}"
        self.set_callback(lambda x: True)

    def relative_time(self, value=None):
        self.title = arrow.get(value).humanize(arrow.utcnow())
        self.set_callback(lambda x: True)

    def money(self, value=None):
        self.title = f"{value:.5f}$"
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
    threads: Optional[int] = None
    remote_hr: Optional[float] = None

    @property
    def display(self):
        parts = filter(lambda x: x[1], [
            ("HR", f"{self.local_hr:.2f}" if self.local_hr else None),
            ("TH", f"{self.threads:.0f}" if self.threads else None),
            ("RHR", f"{self.remote_hr:.2f}" if self.remote_hr else None),
        ])

        return " | ".join([": ".join(p) for p in parts])
