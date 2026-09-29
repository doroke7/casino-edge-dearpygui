from pb.ir.table.inference.game import baccarat_pb2, baccarat_pb2_grpc
from src.service.abstract_service import AbstractServicer


class BaccaratServicer(AbstractServicer, baccarat_pb2_grpc.BaccaratServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizePoker(self, request, context):
        self._grab_frame(context, "baccarat_poker")
        return baccarat_pb2.BaccaratRecognizePokerResponse()

    def RecognizeObject(self, request, context):
        self._grab_frame(context, "baccarat_scene")
        yield baccarat_pb2.BaccaratRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        self._grab_frame(context, "baccarat_all")
        return baccarat_pb2.BaccaratRecognizeAllResponse()
