from pathlib import Path

from dependency_injector import containers, providers

from bootstrap.config import config
from lib.frame_buffer import FrameBuffer
from src.app.snapshot import SnapshotWriter
from src.classifier import PokerCardClassifier, PokerRankClassifier, PokerSuitClassifier
from src.detector import PokerCardDetector
from src.pipeline import PokersPipeline
from src.service.die_service import DieServicer
from src.service.disk_service import DiskServicer
from src.service.poker_service import PokerServicer

RUNTIME_DIR = Path(__file__).resolve().parents[1] / config("recognition.runtime_dir", "runtime")


class RecognitionContainer(containers.DeclarativeContainer):
    # Empty unless something feeds it (the desktop app in `all`; override to share one).
    frames = providers.Singleton(FrameBuffer)

    snapshots = providers.Singleton(SnapshotWriter, RUNTIME_DIR)

    poker_card_detector = providers.Singleton(PokerCardDetector)
    poker_card_classifier = providers.Singleton(PokerCardClassifier)
    poker_rank_classifier = providers.Singleton(PokerRankClassifier)
    poker_suit_classifier = providers.Singleton(PokerSuitClassifier)
    pokers_pipeline = providers.Singleton(
        PokersPipeline,
        poker_card_detector,
        poker_card_classifier,
        poker_rank_classifier,
        poker_suit_classifier,
    )

    poker_servicer = providers.Singleton(PokerServicer, frames, snapshots, pokers_pipeline)
    # The disk and die pipelines are not implemented yet (their files are empty).
    disk_servicer = providers.Singleton(DiskServicer, frames, snapshots, None)
    die_servicer = providers.Singleton(DieServicer, frames, snapshots, None)
