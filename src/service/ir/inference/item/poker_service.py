import threading

from pb.recognition.ir.inference.item import poker_pb2, poker_pb2_grpc
from src.service.abstract_service import AbstractServicer, interval_seconds

INTERVAL_SECONDS = interval_seconds("items.poker.interval")


class PokerServicer(AbstractServicer, poker_pb2_grpc.PokerServiceServicer):
    """Streams the pokers found in the latest camera frame, one response per second."""

    def RecognizeItems(self, request, context):
        stopped = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            yield poker_pb2.PokerRecognizeItemsResponse(items=self._recognize_pokers(self._latest_frame(context)))
            stopped.wait(INTERVAL_SECONDS)
