"""Abstract base class for OpenVINO image classifiers.

Holds the shared model loading, preprocessing and inference logic.
Subclass this for each classify domain (poker card, rank, suit, …).
"""

from __future__ import annotations

import abc
import logging
import os
import threading
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np
import yaml
from openvino import Core

import bootstrap


class AbstractClassifier(abc.ABC):
    """基於 OpenVINO 的圖像分類器基底類別"""

    def __init__(self, model_dir: str, conf_threshold: float = 0.7, ovdevice: str = "CPU", mode: Optional[str] = None):
        """初始化 YOLO26 目標檢測器
        
        Args:
            model_dir: 模型資料夾路徑，包含 best.xml 或 last.xml 和 metadata.yaml
            conf_threshold: 置信度閾值，默認為 0.7
            ovdevice: OpenVINO 推論裝置
            mode: 載入模式，'eager' 建構時預先載入、'lazy' 首次呼叫時才載入；
                未指定時取自 openvino.mode，默認 eager
        """

        self.model_dir = model_dir
        self.conf_threshold = conf_threshold
        # OpenVINO 以大小寫區分裝置名（例如須為 CPU 而非 cpu）
        self.ov_device = ovdevice.strip().upper()
        self._load_lock = threading.Lock()
        self._loaded = False

        mode = str(mode if mode is not None else bootstrap.config('openvino.mode', 'eager')).strip().lower()
        if mode not in ("eager", "lazy"):
            raise ValueError(f"openvino.mode 只能是 eager 或 lazy: {mode}")
        self.mode = mode
        if mode == "eager":
            self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            with self._load_lock:
                if not self._loaded:
                    self._load()

    def _load(self) -> None:
        """載入並編譯模型；eager 模式於建構時呼叫，lazy 模式於首次推論時呼叫"""
        model_dir = self.model_dir

        # 檢查資料夾是否存在
        if not os.path.exists(model_dir):
            raise FileNotFoundError(f"模型資料夾不存在: {model_dir}")

        # 尋找模型檔案
        model_path = None
        for model_name in ["best.xml", "last.xml"]:
            path = os.path.join(model_dir, model_name)
            if os.path.exists(path):
                model_path = path
                break
        
        if model_path is None:
            raise FileNotFoundError(f"在 {model_dir} 中找不到 best.xml 或 last.xml")

        # 讀取 metadata.yaml
        metadata_path = os.path.join(model_dir, "metadata.yaml")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"找不到 metadata.yaml: {metadata_path}")

        with open(metadata_path, "r") as f:
            metadata: Dict[str, Any] = yaml.safe_load(f)

        # 獲取類別名稱
        if "names" not in metadata:
            raise ValueError("metadata.yaml 中缺少 names 欄位")
        
        # 直接使用 names 字典
        self.class_names: Dict[int, str] = metadata["names"]

        # 檢查類別名稱字典
        if not self.class_names:
            raise ValueError("類別名稱字典不能為空")

        # 從 metadata 中獲取輸入尺寸
        if "imgsz" not in metadata:
            raise ValueError("metadata.yaml 中缺少 imgsz 欄位")
        imgsz = metadata["imgsz"]

        # 檢查 imgsz 是否為包含兩個元素的列表
        if not isinstance(imgsz, list) or len(imgsz) != 2:
            raise ValueError("imgsz 必須是包含兩個元素的列表")

        # 初始化 OpenVINO 運行時
        self.core = Core()

        # 載入模型
        self.model = self.core.read_model(model_path)

        # 設置固定輸入形狀 (NCHW 格式)
        input_shape = [1, 3, imgsz[0], imgsz[1]]
        self.model.reshape({0: input_shape})

        # 編譯模型
        self.compiled_model = self.core.compile_model(self.model, self.ov_device)

        # 獲取輸入輸出資訊
        # 輸入層
        self.input_layer = self.compiled_model.input(0)
        # 輸出層
        self.output_layer = self.compiled_model.output(0)

        logging.info(f"====================================================")
        logging.info(f"模型類別: {type(self).__name__}")
        logging.info(f"模型輸入尺寸: {input_shape}")
        logging.info(f"模型輸出尺寸: {self.output_layer.shape}")
        logging.info(f"模型類別數量: {len(self.class_names)}")
        logging.info("模型類別映射: %s", self.class_names)
        self._loaded = True

    def __call__(self, img: np.ndarray) -> Tuple[int, str, float]:
        """YOLO26 end2end 輸出預期為 [1, 300, 6] -> (x1, y1, x2, y2, conf, class_id)
        https://docs.ultralytics.com/guides/end2end-detection/#how-end-to-end-detection-works
        Args:
            img: OpenCV 格式的圖片 (numpy.ndarray)
        
        Returns:
            list of (x1, y1, x2, y2 conf, class_id, class_name,) 檢測結果
        """
        
        # lazy 模式下首次呼叫時才載入模型（eager 已載入則直接略過）
        self._ensure_loaded()

        # 預處理圖片
        input_data = self._preprocess_image(img)

        # 執行檢測
        results = self.compiled_model([input_data])[self.output_layer]

        # 後處理結果
        return self._postprocess_results(results)

    def _preprocess_image(self, img: np.ndarray) -> np.ndarray:
        """預處理圖片
        Args:
            img: OpenCV 格式的圖片 (numpy.ndarray)
        
        Returns:
            Tuple[np.ndarray, Tuple[float, int, int]]: 預處理後的圖片和預處理信息
        """
        # 獲取原始圖片尺寸
        orig_h, orig_w = img.shape[:2]
        
        # 獲取模型輸入尺寸
        model_h, model_w = self.input_layer.shape[2:]
        # 計算縮放比例
        scale = min(model_w / orig_w, model_h / orig_h)
        # 計算新的尺寸
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        # 調整圖片大小，保持比例
        unpadded_img = cv2.resize(img, (new_w, new_h))
        # 創建填充後的圖片
        padded_img = np.zeros((model_h, model_w, 3), dtype=np.uint8)

        # 計算填充位置
        top = (model_h - new_h) // 2
        left = (model_w - new_w) // 2

        # 將調整後的圖片放入填充圖片中
        padded_img[top:top + new_h, left:left + new_w] = unpadded_img

        # 轉換為float32並歸一化
        img_array = padded_img.astype(np.float32) / 255.0

        # 調整通道順序為NCHW
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, 0)

        # 返回預處理後的圖片和預處理信息
        return img_array

    def _postprocess_results(self, results: np.ndarray) -> Tuple[int, str, float]:
        """後處理檢測結果
        
        Args:
            results: 模型輸出的原始結果
            
        Returns:
            list of (class_id, class_name, confidence) 分類結果
        """
        
        # 重新組織數據
        results = results[0]  # 移除批次維度
        class_idx = int(np.argmax(results))
        confidence = float(results[class_idx])
        class_name = self.class_names[class_idx]
        return (class_idx, class_name, confidence)
