from pb.ir.table.inference import disk_pb2, disk_pb2_grpc
from src.service.abstract_service import AbstractServicer


class DiskServicer(AbstractServicer, disk_pb2_grpc.DiskServiceServicer):
    """Placeholder: saves the latest camera frame as a JPEG, then returns an empty result until recognition is wired in."""

    def RecognizeDisk(self, request, context):
        self._grab_frame(context, "disk_disk")
        return disk_pb2.DiskRecognizeDiskResponse()

    def RecognizeScene(self, request, context):
        self._grab_frame(context, "disk_scene")
        return disk_pb2.DiskRecognizeSceneResponse()

    def RecognizeAll(self, request, context):
        self._grab_frame(context, "disk_all")
        return disk_pb2.DiskRecognizeAllResponse()
