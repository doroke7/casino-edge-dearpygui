from pathlib import Path

from dependency_injector import containers, providers

from bootstrap.config import config
from lib.frame_buffer.main import FrameBuffer
from src.app.snapshot import SnapshotWriter
from src.classifier import PokerCardClassifier, PokerRankClassifier, PokerSuitClassifier
from src.detector import PokerCardDetector
from src.pipeline import (
    BaccaratPipeline,
    BarajaPipeline,
    BeadPipeline,
    DiePipeline,
    DiskPipeline,
    PokerPipeline,
    SicboPipeline,
    WheelPipeline,
)
from src.service.ir.table.inference.item import die_service as ir_table_inference_item_die_service
from src.service.ir.table.inference.item import disk_service as ir_table_inference_item_disk_service
from src.service.ir.table.inference.item import poker_service as ir_table_inference_item_poker_service
from src.service.ir.monitor.screenshot import capture_service as ir_monitor_screenshot_capture_service
from src.service.ir.table.inference.game import baccarat_service as ir_table_inference_game_baccarat_service
from src.service.ir.table.inference.game import sicbo_service as ir_table_inference_game_sicbo_service

RUNTIME_DIR = Path(__file__).resolve().parents[1] / config("services.recognition.runtime_dir", "runtime")


class RecognitionContainer(containers.DeclarativeContainer):
    # Empty unless something feeds it (the desktop app in `all`; override to share one).
    frames = providers.Singleton(FrameBuffer)

    snapshots = providers.Singleton(SnapshotWriter, RUNTIME_DIR)

    poker_card_detector = providers.Singleton(PokerCardDetector)
    poker_card_classifier = providers.Singleton(PokerCardClassifier)
    poker_rank_classifier = providers.Singleton(PokerRankClassifier)
    poker_suit_classifier = providers.Singleton(PokerSuitClassifier)
    pokers_pipeline = providers.Singleton(
        PokerPipeline,
        poker_card_detector,
        poker_card_classifier,
        poker_rank_classifier,
        poker_suit_classifier,
    )

    die_pipeline = providers.Singleton(DiePipeline)
    disk_pipeline = providers.Singleton(DiskPipeline)
    baccarat_pipeline = providers.Singleton(BaccaratPipeline)
    sicbo_pipeline = providers.Singleton(SicboPipeline)
    baraja_pipeline = providers.Singleton(BarajaPipeline)
    bead_pipeline = providers.Singleton(BeadPipeline)
    wheel_pipeline = providers.Singleton(WheelPipeline)

    ir_table_inference_game_baccarat_servicer = providers.Singleton(ir_table_inference_game_baccarat_service.BaccaratServicer, frames, snapshots, pokers_pipeline, die_pipeline, baccarat_pipeline)
    ir_table_inference_game_sicbo_servicer = providers.Singleton(ir_table_inference_game_sicbo_service.SicboServicer, frames, snapshots, pokers_pipeline, die_pipeline, sicbo_pipeline)

    ir_table_inference_item_poker_servicer = providers.Singleton(ir_table_inference_item_poker_service.PokerServicer, frames, snapshots, pokers_pipeline, die_pipeline)
    ir_table_inference_item_disk_servicer = providers.Singleton(ir_table_inference_item_disk_service.DiskServicer, frames, snapshots, pokers_pipeline, die_pipeline)
    ir_table_inference_item_die_servicer = providers.Singleton(ir_table_inference_item_die_service.DieServicer, frames, snapshots, pokers_pipeline, die_pipeline)

    ir_monitor_screenshot_capture_servicer = providers.Singleton(ir_monitor_screenshot_capture_service.ScreenshotServicer, frames, snapshots)
