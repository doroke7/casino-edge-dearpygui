from typing import Optional, Tuple
import numpy as np
import bootstrap
from src.classifier.abstract_classifier import AbstractClassifier


class PokerCardClassifier(AbstractClassifier):
    """撲克牌牌面類型分類器（Back、Flow、Front），預設從 config 讀取參數"""

    def __init__(
        self,
        model_dir: Optional[str] = None,
        conf_threshold: Optional[float] = None,
        ovdevice: Optional[str] = None,
    ):
        """初始化撲克牌牌面類型分類器；未指定的參數取自 openvino.yaml

        Args:
            model_dir: 模型資料夾路徑，默認 openvino.classify.poker.card.path
            conf_threshold: 置信度閾值，默認 openvino.classify.poker.card.threshold
            ovdevice: OpenVINO 推論裝置，默認 openvino.device
        """
        super().__init__(
            model_dir if model_dir is not None else bootstrap.config('openvino.classify.poker.card.path'),
            conf_threshold if conf_threshold is not None else bootstrap.config('openvino.classify.poker.card.threshold'),
            ovdevice if ovdevice is not None else bootstrap.config('openvino.device'),
        )

    def __call__(self, img: np.ndarray) -> Tuple[int, str, float]:
        """辨識圖片中的撲克牌牌面類型

        Args:
            img: OpenCV 格式的圖片 (numpy.ndarray)

        Returns:
            (class_id, class_name, confidence) 牌面類型分類結果
        """
        return super().__call__(img)
