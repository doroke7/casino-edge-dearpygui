from pb.recognition.ir.monitor.capture import screenshot_pb2, screenshot_pb2_grpc
from src.service.abstract_service import AbstractServicer


class ScreenshotServicer(AbstractServicer, screenshot_pb2_grpc.ScreenshotServiceServicer):
    """Takes a screenshot: saves the latest camera frame as a JPEG in the runtime directory."""

    def __init__(self, frames, snapshots):
        super().__init__(frames, snapshots, None, None)

    def Make(self, request, context):
        self.grab_frame(context, "screenshot")
        return screenshot_pb2.ScreenshotMakeResponse()
