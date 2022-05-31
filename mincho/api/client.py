
from cachable.request import Request

class ClientMeta(type):
    _instance = None

    def __call__(self, *args, **kwds):
        if not self._instance:
            self._instance = super().__call__(*args, **kwds)
        return self._instance


class Client(object, metaclass=ClientMeta):
    pass

# https://api.ethermine.org/miner/9b7774e9C07668d45C984163069014EDf536C00f/currentStats