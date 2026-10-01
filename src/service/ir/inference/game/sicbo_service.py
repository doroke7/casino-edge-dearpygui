import threading

from pb.recognition.ir.inference.game import sicbo_pb2, sicbo_pb2_grpc
from src.service.abstract_service import AbstractServicer, interval_seconds

INTERVAL_SECONDS = interval_seconds("games.sicbo.interval")


class SicboServicer(AbstractServicer, sicbo_pb2_grpc.SicboServiceServicer):
    """Recognizes the dice (die pipeline) and the table objects (sicbo pipeline) in the latest camera frame."""

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline, sicbo_pipeline):
        super().__init__(frames, snapshots, pokers_pipeline, die_pipeline)
        self._sicbo_pipeline = sicbo_pipeline

    def RecognizeItems(self, request, context):
        stopped = threading.Event()
        context.add_callback(stopped.set)
        while not stopped.is_set():
            yield sicbo_pb2.SicboRecognizeItemsResponse(items=self._recognize_dice(self._latest_frame(context)))
            stopped.wait(INTERVAL_SECONDS)

    def RecognizeObjects(self, request, context):
        return sicbo_pb2.SicboRecognizeObjectsResponse(
            objects=self._recognize_objects(self._sicbo_pipeline, self._latest_frame(context))
        )

    def RecognizeAll(self, request, context):
        frame = self._latest_frame(context)
        return sicbo_pb2.SicboRecognizeAllResponse(
            objects=self._recognize_objects(self._sicbo_pipeline, frame),
            items=self._recognize_dice(frame),
        )
