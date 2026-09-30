from abc import ABC

import cv2
import grpc

from bootstrap.config import config
from pb.recognition import ir_pb2



def interval_seconds(key):
    """The streaming interval configured under `key` (milliseconds), in seconds."""
    return float(config(key, 1000)) / 1000


class AbstractServicer(ABC):
    """Shared plumbing for the recognition servicers: the frame buffer, snapshots and every pipeline.

    Only the pokers pipeline is implemented so far; the die pipeline is injected as None until it is.
    """

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline):
        self._frames = frames
        self._snapshots = snapshots
        self._pokers_pipeline = pokers_pipeline
        self._die_pipeline = die_pipeline

    def _latest_frame(self, context):
        """The latest camera frame; aborts the RPC with UNAVAILABLE when there is none."""
        frame = self._frames.latest()
        if frame is None:
            context.abort(grpc.StatusCode.UNAVAILABLE, "camera is off")
        return frame

    def _grab_frame(self, context, label):
        """The latest camera frame, saved as a JPEG named after `label`."""
        frame = self._latest_frame(context)
        self._snapshots.save(frame, label)
        return frame

    def _recognize_pokers(self, frame):
        """The pokers found in a BGR camera `frame`, as protobuf messages."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return [
            ir_pb2.Poker(
                rank=rank_name,
                suit=suit_name,
                x=x1,
                y=y1,
                width=w,
                height=h,
                confidence=card_conf,
            )
            for x1, y1, _x2, _y2, _x, _y, w, h, _card_name, card_conf, suit_name, _suit_conf, rank_name, _rank_conf, *_
            in self._pokers_pipeline.run(frame_rgb)
        ]

    def _recognize_dice(self, frame):
        """The dice found in a BGR camera `frame`, as protobuf messages.

        The die pipeline returns (x1, y1, x2, y2, x, y, w, h, value, confidence) per die.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return [
            ir_pb2.Die(value=str(value), x=x1, y=y1, width=w, height=h, confidence=confidence)
            for x1, y1, _x2, _y2, _x, _y, w, h, value, confidence, *_
            in self._die_pipeline.run(frame_rgb)
        ]

    @staticmethod
    def _recognize_objects(pipeline, frame):
        """The table objects `pipeline` finds in a BGR camera `frame`, as protobuf messages.

        The pipeline returns (x1, y1, x2, y2, x, y, w, h, class_name, confidence) per object.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return [
            ir_pb2.Object(**{"class": class_name}, x=x1, y=y1, width=w, height=h, confidence=confidence)
            for x1, y1, _x2, _y2, _x, _y, w, h, class_name, confidence, *_
            in pipeline.run(frame_rgb)
        ]
