.PHONY: submodule init install dev run desktop buf clean

PY_VERSION := 3.14
PYTHON ?= python3
VENV := .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

DIST_DIR := dist

# ── local dev ────────────────────────────────────────────

submodule:
	git submodule sync --recursive
	git submodule update --init --recursive --remote



init:
	@rm -Rf .venv
	@uv venv .venv --python $(PY_VERSION)
	@uv venv --seed


# 為什麼用 uv 取代 【pip freeze】或 【pip install pipreqs】
## pip freeze的問題： pip freeze > requirements.txt 。   有依賴樹不准的問題， 問題是 “沒有 lock 文件”
## pip install pipreqs 的問題：pipreqs是透過“代碼分析”去 “猜測” 套件跟版本，並不是直接取得註冊的版本資訊
## uv sync 是透過 pyproject.toml (～= package.json) + uv.lock (～= package-lock.json) 來維持版本號跟依賴樹


## 以往 python 套件管理需要使用各種獨立工具，各種組合拳，使用起來太分散 。uv 解決了這個問題
# 名稱            用途                     傳統用法範例                          uv 用法範例
# --------------  ----------------------  -----------------------------------  -------------------------------
# Python版本管理   管理不同 Python 版本      pyenv install 3.12                  uv python install 3.12
# 虛擬環境         建立獨立 Python 環境      python -m venv .venv               uv venv
# 套件安裝         安裝第三方套件            pip install fastapi                uv add fastapi
# 依賴鎖定         鎖定版本依賴              pip-compile requirements.in        uv lock
# 同步依賴         安裝鎖定後所有依賴         pip-sync                           uv sync
# 執行程式         執行 Python 程式          python main.py desktop                  uv run main.py desktop
# 建置套件         打包 Python 套件          python -m build                    uv build

install:
	@uv sync                        


# 使用虛擬環境的運行
dev:
	@$(PY) main.py recognition -v

run:
	$(PY) main.py recognition -v

desktop:
	$(PY) main.py desktop



# 1. buf generate proto --template buf.gen.yaml
#    會使用 proto 底下的 buf.yaml (即 proto/buf.yaml) 跟 --template指定的 ./buf.gen.yaml 

# 2. 關於 替換 pb代碼的問題：目前 由於 python 有目錄即為 namespace 特性，官方生產的 pb 文件就會帶上 proto 目錄的結構作為命名空間
#    2-a: 解決辦法a: 生成後了全部替換 （確定這個是業界主流做法其中一個）
#    2-b: 解決辦法b: 官方建議 proto 文件的目錄需要跟 “src 目錄一致”，（目錄一致 namespace就自然一致）
#         
#    -- 現在採用簡單暴力法 2-a ，即 全局替換法
buf:
	buf generate proto --template buf.gen.yaml
	find pb -name '*_pb2*.py' -exec sed -i '' -E \
		-e 's/^from (recognition|resource|facade|source)\./from pb.\1./' \
		-e 's/^from (recognition|resource|facade|source) import/from pb.\1 import/' \
		-e 's/^from common import/from pb import/' \
		-e 's/^import common_pb2 as/from pb import common_pb2 as/' \
		{} +


# ── cleanup ──────────────────────────────────────────────


clean:
	rm -rf $(VENV) $(DIST_DIR) build *.egg-info

