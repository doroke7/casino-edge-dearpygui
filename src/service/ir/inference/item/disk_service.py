import threading

from pb.recognition.ir.inference.item import disk_pb2, disk_pb2_grpc
from src.service.abstract_service import AbstractServicer, interval_seconds

INTERVAL_SECONDS = interval_seconds("items.disk.interval")


class DiskServicer(AbstractServicer, disk_pb2_grpc.DiskServiceServicer):
    """Placeholder: streams empty results, saving the latest camera frame as a JPEG each time, until recognition is wired in."""

    def RecognizeItems(self, request, context):
        stopped = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            self._grab_frame(context, "disk")
            yield disk_pb2.DiskRecognizeItemsResponse()
            stopped.wait(INTERVAL_SECONDS)
