from dataclasses_json import Undefined, dataclass_json
from dataclasses import dataclass


@dataclass_json(Undefined.EXCLUDE)
@dataclass
class StatsData:
    time: int
    lastSeen: int
    reportedHashrate: float
    currentHashrate: float
    validShares: int
    invalidShares: int
    staleShares: int
    activeWorkers: int
    averageHashrate: float
    unpaid: int
    coinsPerMin: float
    usdPerMin: float
    btcPerMin: float


@dataclass_json(Undefined.EXCLUDE)
@dataclass
class CurrentStats:
    status: str
    data: StatsData
