import threading

import cv2
from google.protobuf.timestamp_pb2 import Timestamp

from bootstrap.config import config
from pb.recognition import ir_pb2
from pb.recognition.ir.inference.game import sicbo_pb2, sicbo_pb2_grpc
from src.service.abstract_service import AbstractServicer


class SicboServicer(AbstractServicer, sicbo_pb2_grpc.SicboServiceServicer):
    """Recognizes the dice (die pipeline) and the table objects (sicbo pipeline) in the latest camera frame."""

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline, sicbo_pipeline):
        super().__init__(frames, snapshots, pokers_pipeline, die_pipeline)
        self.sicbo_pipeline = sicbo_pipeline

    def RecognizeItems(self, request, context):
        stopped: threading.Event = threading.Event()
        context.add_callback(stopped.set)
        
        while not stopped.is_set():
            o_frame, iTime = self._latest_frame(context)
            o_frame_rgb = cv2.cvtColor(o_frame, cv2.COLOR_BGR2RGB)
            l_results: list = self.die_pipeline.run(o_frame_rgb, iTime)

            l_items: list[ir_pb2.Die] = []
            for o_result in l_results:
                x1 = o_result[0]
                y1 = o_result[1]
                x2 = o_result[2]
                y2 = o_result[3]
                x = o_result[4]
                y = o_result[5]
                w = o_result[6]
                h = o_result[7]
                value = o_result[8]
                confidence = o_result[9]
                o_proto_die = ir_pb2.Die(value=str(value), x=x1, y=y1, width=w, height=h, confidence=confidence)
                l_items.append(o_proto_die)

            o_time: Timestamp = Timestamp()
            o_time.FromNanoseconds(int(iTime * 1_000_000_000))
            yield sicbo_pb2.SicboRecognizeItemsResponse(items=l_items, time=o_time)
            stopped.wait(float(config("games.sicbo.interval", 1000)) / 1000)

    def RecognizeObjects(self, request, context):
        o_frame, iTime = self._latest_frame(context)
        o_frame_rgb = cv2.cvtColor(o_frame, cv2.COLOR_BGR2RGB)
        l_results: list = self.sicbo_pipeline.run(o_frame_rgb, iTime)

        l_objects: list[ir_pb2.Object] = []
        for o_result in l_results:
            x1 = o_result[0]
            y1 = o_result[1]
            x2 = o_result[2]
            y2 = o_result[3]
            x = o_result[4]
            y = o_result[5]
            w = o_result[6]
            h = o_result[7]
            class_name = o_result[8]
            confidence = o_result[9]
            o_proto_object = ir_pb2.Object(**{"class": class_name}, x=x1, y=y1, width=w, height=h, confidence=confidence)
            l_objects.append(o_proto_object)
        o_time: Timestamp = Timestamp()
        o_time.FromNanoseconds(int(iTime * 1_000_000_000))
        return sicbo_pb2.SicboRecognizeObjectsResponse(objects=l_objects, time=o_time)

    def RecognizeAll(self, request, context):
        o_frame, iTime = self._latest_frame(context)
        o_frame_rgb = cv2.cvtColor(o_frame, cv2.COLOR_BGR2RGB)
        l_results: list = self.sicbo_pipeline.run(o_frame_rgb, iTime)

        l_objects: list[ir_pb2.Object] = []
        for o_result in l_results:
            x1 = o_result[0]
            y1 = o_result[1]
            x2 = o_result[2]
            y2 = o_result[3]
            x = o_result[4]
            y = o_result[5]
            w = o_result[6]
            h = o_result[7]
            class_name = o_result[8]
            confidence = o_result[9]
            o_proto_object = ir_pb2.Object(**{"class": class_name}, x=x1, y=y1, width=w, height=h, confidence=confidence)
            l_objects.append(o_proto_object)

        l_results: list = self.die_pipeline.run(o_frame_rgb, iTime)
        l_items: list[ir_pb2.Die] = []
        for o_result in l_results:
            x1 = o_result[0]
            y1 = o_result[1]
            x2 = o_result[2]
            y2 = o_result[3]
            x = o_result[4]
            y = o_result[5]
            w = o_result[6]
            h = o_result[7]
            value = o_result[8]
            confidence = o_result[9]
            o_proto_die = ir_pb2.Die(value=str(value), x=x1, y=y1, width=w, height=h, confidence=confidence)
            l_items.append(o_proto_die)

        o_time: Timestamp = Timestamp()
        o_time.FromNanoseconds(int(iTime * 1_000_000_000))
        return sicbo_pb2.SicboRecognizeAllResponse(objects=l_objects, items=l_items, time=o_time)
