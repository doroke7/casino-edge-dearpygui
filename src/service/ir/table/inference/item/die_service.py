import threading

from bootstrap.config import config
from pb.recognition.ir.inference.item import die_pb2, die_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DieServicer(AbstractServicer, die_pb2_grpc.DieServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeItems(self, request, context):
        stopped: threading.Event = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            self.grab_frame(context, "die")
            yield die_pb2.DieRecognizeItemsResponse()
            stopped.wait(float(config("items.die.interval", 1000)) / 1000)
