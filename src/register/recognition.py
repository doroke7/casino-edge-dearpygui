from container.recognition import RecognitionContainer
from pb.recognition.ir.inference.item import die_pb2_grpc, disk_pb2_grpc, poker_pb2_grpc
from pb.recognition.ir.inference.game import baccarat_pb2_grpc, sicbo_pb2_grpc
from pb.recognition.ir.inference.object import baccarat_pb2_grpc as object_baccarat_pb2_grpc, sicbo_pb2_grpc as object_sicbo_pb2_grpc
from pb.recognition.ir.monitor.capture import screenshot_pb2_grpc


def register(o_server, o_container: RecognitionContainer) -> None:
    """Register every recognition servicer provided by the container on the gRPC server."""
    baccarat_pb2_grpc.add_BaccaratServiceServicer_to_server(o_container.ir_inference_game_baccarat_servicer(), o_server)
    sicbo_pb2_grpc.add_SicboServiceServicer_to_server(o_container.ir_inference_game_sicbo_servicer(), o_server)
    object_baccarat_pb2_grpc.add_BaccaratServiceServicer_to_server(o_container.ir_inference_object_baccarat_servicer(), o_server)
    object_sicbo_pb2_grpc.add_SicboServiceServicer_to_server(o_container.ir_inference_object_sicbo_servicer(), o_server)
    die_pb2_grpc.add_DieServiceServicer_to_server(o_container.ir_inference_item_die_servicer(), o_server)
    disk_pb2_grpc.add_DiskServiceServicer_to_server(o_container.ir_inference_item_disk_servicer(), o_server)
    poker_pb2_grpc.add_PokerServiceServicer_to_server(o_container.ir_inference_item_poker_servicer(), o_server)
    screenshot_pb2_grpc.add_ScreenshotServiceServicer_to_server(o_container.ir_monitor_capture_screenshot_servicer(), o_server)
