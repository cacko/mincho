import rumps
from threading import Thread
from queue import Queue
from mincho.rpc import (
    Client as RPCClient,
    Method as RPCMethod,
    Request,
    Status
)
from mincho import log
from pathlib import Path
from os import environ
from mincho.ui.models import (
    ActionItem,
    BarStats,
    Icon,
    Preset,
    ToggleAction,
)
from mincho.api.client import (
    Client as APIClient
)
from mincho.api.models import (
    CurrentStats,
    Method as APIMethod
)


class MinchoApp(rumps.App):

    rpc_queue: Queue = None
    api_queue: Queue = None
    __connected: bool = None
    __config_path: Path = None
    __rpc_client: RPCClient = None
    __api_client: APIClient = None
    apiStats: CurrentStats = None
    barStats: BarStats = None

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
        self.barStats = BarStats()
        self.__config_path = Path(environ.get(
            "MINCHO_CONFIG", "/Users/jago/.uselethminer/config"))
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

    @rumps.clicked("Default")
    def onDefault(self, sender):
        self.change_preset(Preset.DEFAULT)

    @rumps.clicked("CPU+")
    def onCpu(self, sender):
        self.change_preset(Preset.CPUPLUS)

    @rumps.clicked("Max")
    def onMax(self, sender):
        self.change_preset(Preset.MAXX)

    @rumps.clicked("Stop")
    def onStart(self, sender):
        self.rpc_queue.put_nowait(Request(
            method=RPCMethod.STOP,
        ))

    @rumps.clicked("Start")
    def onStop(self, sender):
        self.rpc_queue.put_nowait(Request(
            method=RPCMethod.START,
        ))

    @rumps.clicked("Quit")
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
        log.debug(res)
        self.status_icon(res.result[0].connected)
        self.barStats.local_hr = sum([r.hashrate for r in res.result]) / 100000
        self.barStats.threads = sum([r.threads_current for r in res.result])

    @rumps.events.on_screen_sleep
    def sleep(self):
        if self.active_preset != Preset.MAXX:
            self.change_preset(Preset.MAXX)

    @rumps.events.on_screen_wake
    def wake(self):
        if self.active_preset != Preset.DEFAULT:
            self.change_preset(Preset.DEFAULT)

    def on_api_response(self, resp):
        self.apiStats = resp
        print(resp)
        self.barStats.remote_hr = resp.data.averageHashrate / 1000000

    # @rumps.clicked("Show all area")
    # def show_area(self, sender):
    #     """ clicked "Show all area button." """
    #     with requests.Session() as s:
    #         area_list = self.get_monitor_area(s)

    #         show_window = rumps.Window(
    #             message='All area name',
    #             title='Area List',
    #             default_text=area_list,
    #             ok=None,
    #             dimensions=(300, 300)
    #         )

    #         show_window.run()

        # self.site_name = response.text
        # self.refresh_status()
