from typing import Optional, Tuple
import numpy as np
import bootstrap
from src.classifier.abstract_classifier import AbstractClassifier


class PokerRankClassifier(AbstractClassifier):
    """撲克牌點數分類器（A、2–10、J、Q、K），預設從 config 讀取參數"""

    def __init__(
        self,
        model_dir: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        ovdevice: Optional[str] = None,
    ):
        """初始化撲克牌點數分類器；未指定的參數取自 openvino.yaml

        Args:
            model_dir: 模型資料夾路徑，默認 openvino.classify.poker.rank.path
            conf_threshold: 置信度閾值，默認 openvino.classify.poker.rank.threshold
            ovdevice: OpenVINO 推論裝置，默認 openvino.device
        """
        super().__init__(
            model_dir if model_dir is not None else bootstrap.config('openvino.classify.poker.rank.path'),
            conf_threshold if conf_threshold is not None else bootstrap.config('openvino.classify.poker.rank.threshold'),
            ovdevice if ovdevice is not None else bootstrap.config('openvino.device'),
        )

    def __call__(self, img: np.ndarray) -> Tuple[int, str, float]:
        """辨識圖片中的撲克牌點數

        Args:
            img: OpenCV 格式的圖片 (numpy.ndarray)

        Returns:
            (class_id, class_name, confidence) 點數分類結果
        """
        return super().__call__(img)
