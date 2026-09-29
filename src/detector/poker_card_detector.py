from typing import List, Optional, Tuple
import numpy as np
import bootstrap
from lib.cache.main import cacheable
from src.detector.abstract_detector import AbstractDetector


class PokerCardDetector(AbstractDetector):
    """撲克牌偵測器，預設從 config 讀取參數"""

    def __init__(
        self,
        model_dir: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        ovdevice: Optional[str] = None,
    ):
        """初始化撲克牌偵測器；未指定的參數取自 openvino.yaml

        Args:
            model_dir: 模型資料夾路徑，默認 openvino.detect.poker.card.path
            conf_threshold: 置信度閾值，默認 openvino.detect.poker.card.thres
            ovdevice: OpenVINO 推論裝置，默認 openvino.device
        """
        super().__init__(
            model_dir if model_dir is not None else bootstrap.config('openvino.detect.poker.card.path'),
            conf_threshold if conf_threshold is not None else bootstrap.config('openvino.detect.poker.card.thres'),
            ovdevice if ovdevice is not None else bootstrap.config('openvino.device'),
        )

    @cacheable(prefix="poker_card_detector", value="", ttl=1)
    def __call__(self, frame_rgb: np.ndarray) -> List[Tuple[int, int, int, int, int, int, int, int, float, int, str]]:
        """偵測圖片中的撲克牌

        Args:
            frame_rgb: RGB 格式的圖片 (numpy.ndarray)

        Returns:
            與 Detector 相同的檢測結果列表
        """
        return super().__call__(frame_rgb)
