from dependency_injector import containers, providers

from src.app.frame_buffer import FrameBuffer
from src.service.die_service import DieServicer
from src.service.disk_service import DiskServicer
from src.service.poker_service import PokerServicer


class RecognitionContainer(containers.DeclarativeContainer):
    # Empty unless something feeds it (the desktop app in `all`; override to share one).
    frames = providers.Singleton(FrameBuffer)

    poker_servicer = providers.Singleton(PokerServicer, frames)
    disk_servicer = providers.Singleton(DiskServicer, frames)
    die_servicer = providers.Singleton(DieServicer, frames)
