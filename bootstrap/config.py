# bootstrap/config.py

from pathlib import Path
import os

import yaml
from dotenv import load_dotenv

# 載入 .env
load_dotenv()

# 全域配置
_CONFIG = {}


# 掃描 config/*.yaml
config_dir = Path(__file__).parent.parent / "config"

for file in config_dir.glob("*.yaml"):
    namespace = file.stem

    with open(file, "r", encoding="utf-8") as f:
        _CONFIG[namespace] = yaml.safe_load(f) or {}



'''

		
### 關於 config 主流的設計模式有兩種

+--------------+----------------------------------------------+----------------------------------------------+
| 模式名稱      | 動態字串路徑尋訪 (String Path Lookup)           | 強型別對象屬性鏈 (Attribute Chaining)           |
+--------------+----------------------------------------------+----------------------------------------------+
| 特性          | 字串鍵值優先 (String-Key Driven)               | 物件型別優先 (Object-Type Driven)              |
+--------------+----------------------------------------------+----------------------------------------------+
| 代碼範例       | config('grpc.port')                          | Config.Grpc.Port                            |
+--------------+----------------------------------------------+----------------------------------------------+
| 結構本質       | 單一大型扁平字典 (Flat Map)                    | 多個自定義類別互相嵌套 (Objects)                |
+--------------+----------------------------------------------+----------------------------------------------+
| IDE 語法提示   | ❌ 完全無提示，全靠盲打拼字                      | ✅ 精準自動補全，層層提示                          |
+--------------+----------------------------------------------+----------------------------------------------+
| 錯誤攔截時機   | 💣 Runtime 延遲引爆（執行到才當機）              | 🔲 Compile-time (編譯時候報錯)                  |
+--------------+----------------------------------------------+----------------------------------------------+
| IDE 標示     | ❌ 拼錯字不會標紅字，語法檢查完全失效               | ⚠️ 拼錯字 Linter 立刻標紅字，拒絕通過編譯         |
+--------------+----------------------------------------------+----------------------------------------------+
| 物件導向封裝   | ❌ 無法將子區塊單獨抽離傳參                      | 支援將 Config.Grpc 子物件單獨傳參                |
+--------------+----------------------------------------------+----------------------------------------------+
| 程式語言偏愛   | PHP, Js, Python                              | Python, Ts, Go, Java, Rust                   |
+--------------+----------------------------------------------+----------------------------------------------+

📌 架構定錨結論：本專案為了維護程式碼全面強制採用 config('grpc.port') 函數，而非 Config.Grpc.Port 結構。


'''



def config(key: str, default=None):
    """
    config("grpc.port")
    config("redis.host")
    """

    # 定義 Python key -> Env key 的邏輯
    # 例如：grpc.port -> GRPC_PORT
    # grpc.max.workers → GRPC_MAX_WORKERS
    # grpc.max_workers → GRPC_MAX_WORKERS
    env_key = key.upper().replace(".", "_")

    if env_key in os.environ:
        return os.environ[env_key]

    try:
        value = _CONFIG

        for part in key.split("."):
            value = value[part]

        return value

    except (KeyError, TypeError):
        return default


def all_config():
    return _CONFIG