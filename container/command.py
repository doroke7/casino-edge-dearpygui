"""Command container — 宣告 command 用到的 pipeline，並把它們注入每個 command。"""

from dependency_injector import containers, providers

from src.classifier import PokerCardClassifier, PokerRankClassifier, PokerSuitClassifier
from src.command import DiePredictorCommand, PokerPredictorCommand
from src.detector import PokerCardDetector
from src.pipeline import DiePipeline, PokerPipeline


class CommandContainer(containers.DeclarativeContainer):

    poker_pipeline = providers.Singleton(
        PokerPipeline,
        providers.Singleton(PokerCardDetector),
        providers.Singleton(PokerCardClassifier),
        providers.Singleton(PokerRankClassifier),
        providers.Singleton(PokerSuitClassifier),
    )

    die_pipeline = providers.Singleton(DiePipeline)

    poker_predictor_command = providers.Singleton(
        PokerPredictorCommand,
        poker_pipeline=poker_pipeline,
    )
    die_predictor_command = providers.Singleton(
        DiePredictorCommand,
        die_pipeline=die_pipeline,
    )
