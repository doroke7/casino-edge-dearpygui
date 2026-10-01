from pb.recognition.ir.inference.object import baccarat_pb2, baccarat_pb2_grpc
from src.service.abstract_service import AbstractServicer


class BaccaratServicer(AbstractServicer, baccarat_pb2_grpc.BaccaratServiceServicer):
    """Recognizes the table objects (baccarat pipeline) in the latest camera frame."""

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline, baccarat_pipeline):
        super().__init__(frames, snapshots, pokers_pipeline, die_pipeline)
        self._baccarat_pipeline = baccarat_pipeline

    def RecognizeObjects(self, request, context):
        return baccarat_pb2.BaccaratRecognizeObjectsResponse(
            objects=self._recognize_objects(self._baccarat_pipeline, self._latest_frame(context))
        )
