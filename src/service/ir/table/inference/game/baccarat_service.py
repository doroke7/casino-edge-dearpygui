import threading

from pb.recognition.ir.inference.game import baccarat_pb2, baccarat_pb2_grpc
from src.service.abstract_service import AbstractServicer, interval_seconds

INTERVAL_SECONDS = interval_seconds("games.baccarat.interval")


class BaccaratServicer(AbstractServicer, baccarat_pb2_grpc.BaccaratServiceServicer):
    """Recognizes the pokers (poker pipeline) and the table objects (baccarat pipeline) in the latest camera frame."""

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline, baccarat_pipeline):
        super().__init__(frames, snapshots, pokers_pipeline, die_pipeline)
        self._baccarat_pipeline = baccarat_pipeline

    def RecognizeItems(self, request, context):
        stopped = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            yield baccarat_pb2.BaccaratRecognizeItemsResponse(items=self._recognize_pokers(self._latest_frame(context)))
            stopped.wait(INTERVAL_SECONDS)

    def RecognizeObjects(self, request, context):
        return baccarat_pb2.BaccaratRecognizeObjectsResponse(
            objects=self._recognize_objects(self._baccarat_pipeline, self._latest_frame(context))
        )

    def RecognizeAll(self, request, context):
        frame = self._latest_frame(context)
        return baccarat_pb2.BaccaratRecognizeAllResponse(
            objects=self._recognize_objects(self._baccarat_pipeline, frame),
            items=self._recognize_pokers(frame),
        )
