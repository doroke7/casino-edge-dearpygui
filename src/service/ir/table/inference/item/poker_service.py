import threading

from bootstrap.config import config
from pb.recognition import ir_pb2
from pb.recognition.ir.inference.item import poker_pb2, poker_pb2_grpc
from src.service.abstract_service import AbstractServicer


class PokerServicer(AbstractServicer, poker_pb2_grpc.PokerServiceServicer):
    """Streams the pokers found in the latest camera frame, one response per second."""

    def RecognizeItems(self, request, context):
        stopped: threading.Event = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            o_frame, iTime = self._latest_frame(context)
            items: list[ir_pb2.Poker] = self._recognize_pokers(o_frame, iTime)
            yield poker_pb2.PokerRecognizeItemsResponse(items=items)
            stopped.wait(float(config("items.poker.interval", 1000)) / 1000)
