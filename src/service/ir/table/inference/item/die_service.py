import threading

from pb.recognition.ir.inference.item import die_pb2, die_pb2_grpc
from src.service.abstract_service import AbstractServicer, interval_seconds

INTERVAL_SECONDS = interval_seconds("items.die.interval")


class DieServicer(AbstractServicer, die_pb2_grpc.DieServiceServicer):
    """Placeholder: streams empty results, saving the latest camera frame as a JPEG each time, until recognition is wired in."""

    def RecognizeItems(self, request, context):
        stopped = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            self._grab_frame(context, "die")
            yield die_pb2.DieRecognizeItemsResponse()
            stopped.wait(INTERVAL_SECONDS)
