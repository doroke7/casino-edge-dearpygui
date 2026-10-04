import threading

from bootstrap.config import config
from pb.recognition.ir.inference.item import disk_pb2, disk_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DiskServicer(AbstractServicer, disk_pb2_grpc.DiskServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeItems(self, request, context):
        stopped: threading.Event = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            self.grab_frame(context, "disk")
            yield disk_pb2.DiskRecognizeItemsResponse()
            stopped.wait(float(config("items.disk.interval", 1000)) / 1000)
