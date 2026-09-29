from pathlib import Path

from dependency_injector import containers, providers

from bootstrap.config import config
from lib.frame_buffer import FrameBuffer
from src.app.snapshot import SnapshotWriter
from src.classifier import PokerCardClassifier, PokerRankClassifier, PokerSuitClassifier
from src.detector import PokerCardDetector
from src.pipeline import PokersPipeline
from src.service.ir.table.inference.equipment import die_service as ir_table_inference_equipment_die_service
from src.service.ir.table.inference.equipment import disk_service as ir_table_inference_equipment_disk_service
from src.service.ir.table.inference.equipment import poker_service as ir_table_inference_equipment_poker_service
from src.service.ir.table.inference.game import baccarat_service as ir_table_inference_game_baccarat_service
from src.service.ir.table.inference.game import sicbo_service as ir_table_inference_game_sicbo_service

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

    ir_table_inference_game_baccarat_servicer = providers.Singleton(ir_table_inference_game_baccarat_service.BaccaratServicer, frames, snapshots, pokers_pipeline)
    # The sicbo pipeline is not implemented yet.
    ir_table_inference_game_sicbo_servicer = providers.Singleton(ir_table_inference_game_sicbo_service.SicboServicer, frames, snapshots, None)

    ir_table_inference_equipment_poker_servicer = providers.Singleton(ir_table_inference_equipment_poker_service.PokerServicer, frames, snapshots, pokers_pipeline)
    # The disk and die pipelines are not implemented yet.
    ir_table_inference_equipment_disk_servicer = providers.Singleton(ir_table_inference_equipment_disk_service.DiskServicer, frames, snapshots, None)
    ir_table_inference_equipment_die_servicer = providers.Singleton(ir_table_inference_equipment_die_service.DieServicer, frames, snapshots, None)
