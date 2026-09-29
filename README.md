## 性能的問題

**測試條件**

- Apple M4（10 核心）、macOS 26.5、內建「MacBook Air相機」
- 擷取 1280x720 @ 30fps（`src/driver/camera.py` 的 `CAMERA_FPS`）；預覽為同一份畫面，由系統 GPU 合成、縮放到視窗大小
- 只開攝影機預覽，沒有錄影、沒有截圖
- 百分比以「一顆核心 = 100%」計，10 核心的機器上 24% 約等於整機 2.4%

**結果**

| | 做法 | CPU（單核 = 100%） | 說明 |
| --- | --- | --- | --- |
| 原生 GPU 疊加 | `AVCaptureVideoPreviewLayer` 貼在視窗的 `NSView` 上，由系統合成，Python 不碰像素 | **~24%** | dearpygui 本身只畫選單列與狀態文字 |

**執行**

```
uv sync
uv run main.py desktop
```

## Recognition gRPC

```
uv run main.py recognition            # 預設 port 見 config/recognition.yaml
```

修改 `proto/` 後重新產生 stub（輸出到 `pb/`）：

```
make buf
```
