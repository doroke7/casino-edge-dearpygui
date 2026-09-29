from dependency_injector import containers, providers

from src.service.die_service import DieServicer
from src.service.disk_service import DiskServicer
from src.service.poker_service import PokerServicer


class RecognitionContainer(containers.DeclarativeContainer):
    poker_servicer = providers.Singleton(PokerServicer)
    disk_servicer = providers.Singleton(DiskServicer)
    die_servicer = providers.Singleton(DieServicer)
