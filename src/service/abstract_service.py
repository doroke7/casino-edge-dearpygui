from abc import ABC

import time

import cv2
import grpc
import numpy as np

from bootstrap.config import config
from pb.recognition import ir_pb2


class AbstractServicer(ABC):
    """Shared plumbing for the recognition servicers: the frame buffer, snapshots and every pipeline.

    Only the pokers pipeline is implemented so far; the die pipeline is injected as None until it is.
    """

    def __init__(self, frames, snapshots, pokers_pipeline, die_pipeline):
        self._frames = frames
        self._snapshots = snapshots
        self._pokers_pipeline = pokers_pipeline
        self.die_pipeline = die_pipeline
        self._cached_frame = None
        self._cached_at = 0.0

    def _latest_frame(self, context) -> tuple[np.ndarray, float]:
        """The latest camera frame and the time it was fetched (epoch seconds), cached for `frame.ttl` seconds.

        Aborts the RPC with UNAVAILABLE when there is no frame.
        """
        now: float = time.time()
        if self._cached_frame is not None and now - self._cached_at < float(config("frame.ttl", 0.3)):
            return self._cached_frame, self._cached_at
        o_frame: np.ndarray = self._frames.latest()
        if o_frame is None:
            context.abort(grpc.StatusCode.UNAVAILABLE, "camera is off")
        self._cached_frame = o_frame
        self._cached_at = now
        return o_frame, now

    def grab_frame(self, context, label):
        """The latest camera frame, saved as a JPEG named after `label`."""
        o_frame, _ = self._latest_frame(context)
        self._snapshots.save(o_frame, label)
        return o_frame

    def _recognize_pokers(self, frame, iTime):
        """The pokers found in a BGR camera `frame` fetched at `iTime`, as protobuf messages."""
        frame_rgb: np.ndarray = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
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
            in self._pokers_pipeline.run(frame_rgb, iTime)
        ]
