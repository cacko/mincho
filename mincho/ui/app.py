import rumps
from threading import Thread
from queue import Queue
from mincho.rpc import (
    Client as RPCClient,
    Method as RPCMethod,
    Request,
    Status
)
from pathlib import Path
from mincho.ui.models import (
    ActionItem,
    ApiStats,
    BarStats,
    Icon,
    Label,
    Preset,
    StatItem,
    ToggleAction,
)
from mincho.api.client import (
    Client as APIClient
)
from mincho.api.models import (
    Method as APIMethod
)
from mincho import app_config


class MinchoApp(rumps.App):

    rpc_queue: Queue = None
    api_queue: Queue = None
    __connected: bool = None
    __config_path: Path = None
    __rpc_client: RPCClient = None
    __api_client: APIClient = None
    apiStats: ApiStats = None
    barStats: BarStats = None

    def __init__(self):
        super(MinchoApp, self).__init__(
            name="Mincho",
            menu=[
                StatItem.active_workers,
                StatItem.last_seen,
                StatItem.usd_per_minute,
                StatItem.current_hashrate,
                StatItem.threads,
                None,
                ActionItem.default,
                ActionItem.cpuplus,
                ActionItem.max,
                None,
                ToggleAction.start,
                ToggleAction.stop,
                ActionItem.quit
            ],
            quit_button=None
        )
        self.barStats = BarStats()
        self.__config_path = Path(app_config.mincho_config)
        self.menu.setAutoenablesItems = False
        ActionItem.stop.hide()
        ActionItem.start.hide()
        self.__rpc_client = RPCClient(self)
        self.rpc_queue = self.__rpc_client.input
        t = Thread(target=self.__rpc_client.start)
        t.start()
        self.__api_client = APIClient(self.on_api_response)
        self.api_queue = self.__api_client.input
        t2 = Thread(target=self.__api_client.start)
        t2.start()

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
        if self.active_preset == cfg:
            return
        getattr(ActionItem, self.active_preset.value).state = 0
        parent = self.__config_path.parent
        new_config: Path = parent / cfg.value
        self.__config_path.unlink()
        self.__config_path.symlink_to(new_config)
        self.rpc_queue.put_nowait(Request(method=RPCMethod.SHUTDOWN))

    @rumps.clicked(Label.DEFAULT.value)
    def onDefault(self, sender):
        self.change_preset(Preset.DEFAULT)

    @rumps.clicked(Label.CPUPLUS.value)
    def onCpu(self, sender):
        self.change_preset(Preset.CPUPLUS)

    @rumps.clicked(Label.MAX.value)
    def onMax(self, sender):
        self.change_preset(Preset.MAXX)

    @rumps.clicked(Label.STOP.value)
    def onStart(self, sender):
        self.rpc_queue.put_nowait(Request(
            method=RPCMethod.STOP,
        ))

    @rumps.clicked(Label.START.value)
    def onStop(self, sender):
        self.rpc_queue.put_nowait(Request(
            method=RPCMethod.START,
        ))

    @rumps.clicked(Label.QUIT.value)
    def onQuit(self, sender):
        rumps.quit_application()

    @rumps.timer(5)
    def updateStatus(self, sender):
        if self.__rpc_client.connected:
            self.rpc_queue.put_nowait(
                Request(method=RPCMethod.STATUS)
            )
            self.title = self.barStats.display

    @rumps.timer(300)
    def updateApiStats(self, sender):
        self.api_queue.put_nowait(APIMethod.STATS)

    def onResult(self, method: RPCMethod, res: str):
        match(method):
            case RPCMethod.STATUS:
                return self.on_status(Status.from_json(res))

    def status_icon(self, status: bool):
        if status != self.__connected:
            self.__connected = status
            icon = Icon.ON if status else Icon.OFF
            self.icon = icon.value
            ToggleAction.start.toggle(not self.__connected)
            ToggleAction.stop.toggle(self.__connected)
            if self.__connected:
                try:
                    getattr(ActionItem, self.active_preset.value).state = 1
                except Exception as e:
                    print(e)

    def on_status(self, res: Status):
        self.status_icon(res.result[0].connected)
        self.barStats.local_hr = sum([r.hashrate for r in res.result]) / 100000
        self.barStats.preset = self.active_preset.value
        StatItem.threads.number(sum([r.threads_current for r in res.result]))

    @rumps.events.on_screen_sleep
    def sleep(self):
        if self.active_preset != Preset.MAXX:
            self.change_preset(Preset.MAXX)

    @rumps.events.on_screen_wake
    def wake(self):
        if self.active_preset != Preset.DEFAULT:
            self.change_preset(Preset.DEFAULT)

    def on_api_response(self, resp: ApiStats):
        self.apiStats: ApiStats = resp
        self.barStats.remote_hr = resp.averageHashrate / 1000000
        StatItem.active_workers.number(self.apiStats.activeWorkers)
        StatItem.last_seen.relative_time(self.apiStats.lastSeen)
        StatItem.usd_per_minute.money(self.apiStats.usdPerMin)
        StatItem.current_hashrate.hashrate(resp.currentHashrate)
