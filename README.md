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

## Command（離線辨識）

對一個目錄底下的圖片（只讀第一層，支援 `.jpg` `.jpeg` `.png` `.bmp` `.webp`）跑辨識，依檔名順序印出結果與耗時報告。

```
uv run main.py command poker-predictor --workdir ./runtime/poker
uv run main.py command die-predictor   --workdir ./runtime/die --threads 8
```

| 指令 | 說明 |
| --- | --- |
| `poker-predictor` | 辨識撲克牌：牌面、花色、點數與信心值、座標框 |
| `die-predictor` | 辨識骰子（pipeline 目前是佔位實作，一律偵測到 0 顆） |

| 參數 | 說明 |
| --- | --- |
| `--workdir` | 必填，圖片目錄（必須已存在） |
| `--threads` | 同時辨識的執行緒數量，預設 4 |

列出所有指令：`uv run main.py command --help`

## 目錄說明

```
.
├── main.py                 # 程式入口（click 指令集合：desktop / recognition / all）
├── Makefile                # 常用指令：install、desktop、run、buf（產生 pb）、clean
├── pyproject.toml / uv.lock  # 依賴宣告與鎖定（uv 管理）
├── buf.gen.yaml            # buf 產生 Python stub 的模板
├── .gitmodules             # 子模組：proto、sample
│
├── cli/                    # 命令列子指令 (～= golang 的 cmd)
│   ├── root.py             #   指令群組，註冊各子指令
│   ├── desktop/            #   desktop：桌面攝影機預覽（dearpygui）
│   ├── recognition/        #   recognition：啟動辨識 gRPC 服務
│   ├── command/            #   command：離線辨識（poker-predictor、die-predictor）
│   └── all/                #   all：桌面 + gRPC 同時啟動，共用攝影機畫面
│
├── bootstrap/              # 啟動初始化（載入 config 等）
├── container/              # DI 依賴注入容器（desktop.py、recognition.py）
├── config/                 # YAML 設定
│   ├── desktop.yaml        #   桌面端
│   ├── services.yaml       #   gRPC 服務（port、workers、runtime 目錄）
│   ├── openvino.yaml       #   OpenVINO 推論
│   └── games.yaml / items.yaml  # 遊戲與物件定義
│
├── src/                    # 主要業務程式 (～= golang 的 internal)
│   ├── app/                #   桌面應用：desktop、main_thread、camera_controller、snapshot（截圖存 JPEG）
│   ├── ui/                 #   dearpygui 介面（menu 選單列、status 狀態文字）
│   ├── driver/camera.py    #   攝影機驅動（解析度、FPS）
│   ├── command/            #   command 類別（各自獨立，不共用實作）
│   ├── service/            #   gRPC servicer 實作（ir/table/inference/{game,item}、ir/monitor/screenshot）
│   ├── register/           #   把 servicer 註冊到 gRPC server
│   ├── pipeline/           #   各遊戲/物件辨識流程（baccarat、sicbo、poker、die、disk、wheel、bead、baraja）
│   ├── detector/           #   偵測器（撲克牌偵測）
│   └── classifier/         #   分類器（撲克牌、點數、花色）
│ 
├── lib/                    # 通用工具 (～= golang 的 pkg)
│   ├── frame_buffer/       #   只保留最新一幀，供擷取執行緒與讀取端共享
│   ├── cache/              #   記憶體快取
│   └── utility/            #   小工具（如 pad_box）
│
├── proto/                  # protobuf 定義（git submodule）
├── pb/                     # 由 proto 產生的 gRPC stub（勿手改，用 `make buf` 重新產生）
├── sample/                 # Python 範例集（git submodule）
├── asset/                  # 靜態資源（icon.png）
└── runtime/                # 執行期輸出（如截圖），內容不進版控
```
