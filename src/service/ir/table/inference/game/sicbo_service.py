from pb.ir.table.inference.game import sicbo_pb2, sicbo_pb2_grpc
from src.service.abstract_service import AbstractServicer


class SicboServicer(AbstractServicer, sicbo_pb2_grpc.SicboServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeDie(self, request, context):
        self._grab_frame(context, "sicbo_die")
        return sicbo_pb2.SicboRecognizeDieResponse()

    def RecognizeObject(self, request, context):
        self._grab_frame(context, "sicbo_scene")
        yield sicbo_pb2.SicboRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        self._grab_frame(context, "sicbo_all")
        return sicbo_pb2.SicboRecognizeAllResponse()
