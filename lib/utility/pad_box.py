from __future__ import annotations

from typing import Tuple

import cv2
import numpy


def pad_box(
    frame: numpy.ndarray,
    output_size: Tuple[int, int],
    *,
    pad_value: int = 0,
) -> Tuple[numpy.ndarray, Tuple[float, int, int, int, int]]:
    """
    等比縮放圖像到目標大小（aspect fit），不足處以 pad_value 補邊。
    input 比 target 小時會放大，比 target 大時會縮小。

    參數:
        frame: 輸入圖像
        output_size: 輸出圖像大小 (寬度, 高度)
        pad_value: 補邊像素值，預設 0（黑）

    返回:
        (縮放補邊後的圖像, (scale, left, top, orig_w, orig_h))
    """
    h, w = frame.shape[:2]
    target_w, target_h = output_size
    if w == 0 or h == 0 or target_w == 0 or target_h == 0:
        return frame, (1.0, 0, 0, w, h)
    if h == target_h and w == target_w:
        return frame, (1.0, 0, 0, w, h)

    scale = min(target_w / w, target_h / h)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(frame, (new_w, new_h), interpolation=interp)

    if new_w == target_w and new_h == target_h:
        padded = resized
        left, top = 0, 0
    else:
        padded = numpy.full((target_h, target_w, 3), pad_value, dtype=frame.dtype)
        left = (target_w - new_w) // 2
        top = (target_h - new_h) // 2
        padded[top : top + new_h, left : left + new_w] = resized

    return padded, (scale, left, top, w, h)
