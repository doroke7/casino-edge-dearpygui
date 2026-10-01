from pb.recognition.ir.inference.object import sicbo_pb2, sicbo_pb2_grpc
from src.service.abstract_service import AbstractServicer


class SicboServicer(AbstractServicer, sicbo_pb2_grpc.SicboServiceServicer):
    """Recognizes the table objects (sicbo pipeline) in the latest camera frame."""

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline, sicbo_pipeline):
        super().__init__(frames, snapshots, pokers_pipeline, die_pipeline)
        self._sicbo_pipeline = sicbo_pipeline

    def RecognizeObjects(self, request, context):
        return sicbo_pb2.SicboRecognizeObjectsResponse(
            objects=self._recognize_objects(self._sicbo_pipeline, self._latest_frame(context))
        )
