"""Abstract base class for OpenVINO object detectors.

Holds the shared model loading, preprocessing and inference logic.
Subclass this for each detect domain (poker card, …).
"""

from __future__ import annotations

import abc
import logging
import os
import threading
from typing import Any, Dict, Optional, List, Tuple

import cv2
import numpy as np
import yaml
from openvino import Core

import bootstrap

from lib.utility import pad_box


class AbstractDetector(abc.ABC):
    """基於 OpenVINO 的 YOLO26 目標檢測器基底類別"""

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
        self.conf_threshold = float(conf_threshold)
        # OpenVINO 以大小寫區分裝置名（例如須為 CPU 而非 cpu）
        self.ov_device = ovdevice.strip().upper()
        self._load_lock = threading.Lock()
        self._loaded = False
        self._request_local = threading.local()

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

    def _infer(self, input_data: np.ndarray) -> np.ndarray:
        """用目前這個執行緒自己的 infer request 推論。

        compiled_model([...]) 底下共用同一個 infer request，多執行緒同時呼叫會拋
        "Infer Request is busy"，所以每個執行緒各建一個。
        """
        request = getattr(self._request_local, "request", None)
        if request is None:
            request = self.compiled_model.create_infer_request()
            self._request_local.request = request
        return request.infer([input_data])[self.output_layer]

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
        # 是否需要 NMS (end2end 輸出預期為 [1, 300, 6] -> (x1, y1, x2, y2, conf, class_id))
        self.need_nms = self.output_layer.shape[2] != 6
        logging.info(f"====================================================")
        logging.info(f"模型類別: {type(self).__name__}")
        logging.info(f"模型輸入尺寸: {input_shape}")
        logging.info(f"模型輸出尺寸: {self.output_layer.shape}")
        logging.info(f"模型類別數量: {len(self.class_names)}")
        logging.info("模型類別映射: %s", self.class_names)
        self._loaded = True

    def __call__(self, frame_rgb: np.ndarray) -> List[Tuple[int, int, int, int, int, int, int, int, float, int, str]]:
        """YOLO26 end2end 輸出預期為 [1, 300, 6] -> (x1, y1, x2, y2, conf, class_id)
        https://docs.ultralytics.com/guides/end2end-detection/#how-end-to-end-detection-works
        Args:
            frame_rgb: H, W, 3 的 uint8 類型的 RGB 格式的圖像 (numpy.ndarray)
        
        Returns:
            list of (x1, y1, x2, y2 conf, class_id, class_name,) 檢測結果
        """
        
        # lazy 模式下首次呼叫時才載入模型（eager 已載入則直接略過）
        self._ensure_loaded()

        # 預處理圖片
        input_data, preprocess_info = self._preprocess_image(frame_rgb)

        # 執行檢測
        results = self._infer(input_data)

        # 後處理結果
        if self.need_nms:
            return self._postprocess_nms_results(results, preprocess_info)
        else:
            return self._postprocess_results(results, preprocess_info)

    def _preprocess_image(self, frame_rgb: np.ndarray) -> Tuple[np.ndarray, Tuple[float, int, int, int, int]]:
        """預處理圖片
        Args:
            frame_rgb: H, W, 3 的 uint8 類型的 RGB 格式的圖像 (numpy.ndarray)

        Returns:
            預處理後的圖片和預處理信息 (scale, left, top, orig_w, orig_h)
        """
        model_h, model_w = self.input_layer.shape[2:]
        padded_img, preprocess_info = pad_box(frame_rgb, (model_w, model_h))

        # 轉換為float32並歸一化
        img_array = padded_img.astype(np.float32) / 255.0

        # 調整通道順序為NCHW
        img_array = np.transpose(img_array, (2, 0, 1))
        img_array = np.expand_dims(img_array, 0)

        # 返回預處理後的圖片和預處理信息
        return img_array, preprocess_info

    def _postprocess_results(self, results: np.ndarray, preprocess_info: Tuple[float, int, int, int, int]) -> List[Tuple[int, int, int, int, int, int, int, int, float, int, str]]:
        """後處理檢測結果
        
        Args:
            results: 模型輸出的原始結果
            img_size: 原始圖片尺寸 (width, height)
            preprocess_info: 預處理信息 (scale, left, top, orig_w, orig_h)
            
        Returns:
            list of (x1, y1, x2, y2, x, y, w, h, conf, class_id, class_name) 檢測結果
        """
        detections = []
        
        # 獲取預處理信息
        scale, left, top, orig_w, orig_h = preprocess_info
        
        # 重新組織數據
        results = results[0]  # 移除批次維度

        # 處理每個檢測結果
        for i in range(len(results)):
            x1, y1, x2, y2, conf, class_id = results[i, :6]
            if conf < self.conf_threshold:
                continue
            
            # 將中心點座標轉換為實際圖像尺寸
            x1 = max(0, int(min((x1 - left) / scale, orig_w)))
            y1 = max(0, int(min((y1 - top) / scale, orig_h)))
            x2 = max(0, int(min((x2 - left) / scale, orig_w)))
            y2 = max(0, int(min((y2 - top) / scale, orig_h)))

            # 獲取類別名稱
            try:
                class_id = int(class_id)
                class_name = self.class_names[class_id]
            except KeyError:
                logging.warning(f"警告: 類別索引 {class_id} 不存在，跳過此檢測結果")
                continue
            detections.append((x1, y1, x2, y2, x1 + (x2 - x1)/2, y1 + (y2 - y1)/2, x2 - x1, y2 - y1, conf, class_id, class_name))

        return detections

    def _postprocess_nms_results(self, results: np.ndarray, preprocess_info: Tuple[float, int, int, int, int]) -> List[Tuple[int, int, int, int, int, int, int, int, float, int, str]]:
        """後處理檢測結果
        
        Args:
            results: 模型輸出的原始結果
            img_size: 原始圖片尺寸 (width, height)
            preprocess_info: 預處理信息 (scale, left, top)
            
        Returns:
            list of (x1, y1, x2, y2, x, y, w, h, conf, class_id, class_name) 檢測結果
        """
        detections = []
                
        # 獲取預處理信息
        scale, left, top, orig_w, orig_h = preprocess_info
        
        # 重新組織數據
        results = results[0]  # 移除批次維度
        num_classes = results.shape[0] - 5  # 計算類別數量
        
        # 提取邊界框和置信度
        boxes = results[:4, :]  # [4, 8400]
        confidences = results[4, :]  # [8400]
        
        if num_classes > 0:
            class_scores = results[5:, :]  # [num_classes, 8400]
            class_scores = class_scores.transpose()  # [8400, num_classes]
            class_ids = np.argmax(class_scores, axis=1)  # [8400]
            class_scores = np.max(class_scores, axis=1)  # [8400]
            confidences = confidences * class_scores
        else:
            class_ids = np.zeros(confidences.shape, dtype=np.int32)
        
        # 轉置邊界框為 [8400, 4]
        boxes = boxes.transpose()
        
        # 準備 NMS 的輸入數據
        nms_boxes = []
        nms_confidences = []
        nms_class_ids = []
        
        # 處理每個檢測結果
        for i in range(len(boxes)):
            if confidences[i] < self.conf_threshold:
                continue
                
            # 獲取邊界框座標 (x, y, w, h)
            x, y, w, h = boxes[i]
            
            # 將中心點座標轉換為實際圖像尺寸
            x = int((x - left) / scale)
            y = int((y - top) / scale)
            w = int(w / scale)
            h = int(h / scale)
            
            # 獲取類別名稱
            try:
                class_id = int(class_ids[i])
                class_name = self.class_names[class_id]
            except KeyError:
                logging.warning(f"警告: 類別索引 {class_id} 不存在，跳過此檢測結果")
                continue
            
            # 添加到 NMS 輸入數據
            nms_boxes.append([x, y, w, h])
            nms_confidences.append(float(confidences[i]))
            nms_class_ids.append(class_id)
        
        # 應用 NMS
        if len(nms_boxes) > 0:
            # 使用 cv2.dnn.NMSBoxes 進行非極大值抑制
            indices = cv2.dnn.NMSBoxes(nms_boxes, nms_confidences, self.conf_threshold, 0.7)
            
            # 整理最終檢測結果
            for i in indices:
                x, y, w, h = nms_boxes[i]
                class_id = nms_class_ids[i]
                class_name = self.class_names[class_id]
                conf = nms_confidences[i]
                detections.append((x - w/2, y - h/2, x + w/2, y + h/2, x, y, w, h, conf, class_id, class_name))
            
        return detections