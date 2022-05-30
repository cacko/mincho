import rumps
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
from os import environ
from mincho.ui.models import (
    ActionItem,
    Icon,
    Preset,
    ToggleAction
)


class MinchoApp(rumps.App):

    queue: Queue = None
    __connected: bool = False
    __config_path: Path = None
    __rpc_client: Client = None

    def __init__(self):
        super(MinchoApp, self).__init__(
            name="Mincho",
            menu=[
                ToggleAction.start,
                ToggleAction.stop,
                None,
                ActionItem.default,
                ActionItem.cpuplus,
                ActionItem.max,
                None,
            ],
            quit_button=None
        )
        self.__config_path = Path(environ.get(
            "MINCHO_CONFIG", "/Users/jago/.uselethminer/config"))
        ActionItem.start.hide()
        self.__rpc_client = Client(self)
        self.queue = self.__rpc_client.input
        t = Thread(target=self.__rpc_client.start)
        t.start()

    @property
    def active_preset(self) -> Preset:
        if not self.__config_path.exists():
            return None
        cfp = self.__config_path.resolve().name
        try:
            return Preset(cfp)
        except ValueError:
            return None

    def change_preset(self, cfg: Preset):
        getattr(ActionItem, self.active_preset.value).state = 0
        parent = self.__config_path.parent
        new_config: Path = parent / cfg.value
        self.__config_path.unlink()
        self.__config_path.symlink_to(new_config)

    @rumps.clicked("Default")
    def onDefault(self, sender):
        self.change_preset(Preset.DEFAULT)
        self.queue.put_nowait(Request(method=Method.SHUTDOWN))

    @rumps.clicked("CPU+")
    def onCpu(self, sender):
        self.change_preset(Preset.CPUPLUS)
        self.queue.put_nowait(Request(method=Method.SHUTDOWN))

    @rumps.clicked("Max")
    def onMax(self, sender):
        self.change_preset(Preset.MAXX)
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

    @rumps.clicked("Quit")
    def onQuit(self, sender):
        rumps.quit_application()

    @rumps.timer(5)
    def updateStatus(self, sender):
        if self.__rpc_client.connected:
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
            self.icon = icon.value
            ToggleAction.start.toggle()
            ToggleAction.stop.toggle()
            if self.__connected:
                try:
                    getattr(ActionItem, self.active_preset.value).state = 1
                except Exception as e:
                    print(e)

    def on_status(self, res: Status):
        log.debug(res)
        self.status_icon(res.result[0].connected)
        hash_rate = [f"{r.hashrate / 100000:.2f}" for r in res.result]
        threads = [f"{r.threads_current}" for r in res.result]
        self.title = f"HR: {' '.join(hash_rate)} | TH: {' '.join(threads)}"
