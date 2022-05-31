import logging
from os import environ
from mincho.core.config import Config


logging.basicConfig(
    level=getattr(logging, environ.get("MINCHO_LOG_LEVEL", "INFO")),
    format="%(filename)s %(message)s",
    datefmt="MINCH %H:%M:%S",
)
log = logging.getLogger("BOTYO")


class app_config_meta(type):
    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance

    @property
    def client_id(cls):
        return cls().get_var("CLIENT_ID")

    @property
    def mincho_config(cls):
        return cls().get_var("MINCHO_CONFIG")


class app_config(object, metaclass=app_config_meta):

    _config = None

    def __init__(self) -> None:
        self._config = Config()
        self._config.from_pyfile("config.py")

    def get_var(self, var):
        return self._config.get(var)
