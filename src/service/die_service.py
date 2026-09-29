from pb.ir.table.inference import die_pb2, die_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DieServicer(AbstractServicer, die_pb2_grpc.DieServiceServicer):
    """Placeholder: needs a camera frame, then returns an empty result until recognition is wired in."""

    def RecognizeDie(self, request, context):
        self._grab_frame(context)
        return die_pb2.DieRecognizeDieResponse()

    def RecognizeScene(self, request, context):
        self._grab_frame(context)
        return die_pb2.DieRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        self._grab_frame(context)
        return die_pb2.DieRecognizeAllResponse()
