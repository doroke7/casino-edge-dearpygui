import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import click
import cv2
import openvino

import bootstrap
from src.command.abstract_command import AbstractCommand, BoundCommand
from src.pipeline import AbstractPipeline

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

RESULT_KEYS = (
    "x1", "y1", "x2", "y2", "x", "y", "w", "h",
    "name", "confidence",
    "suit", "suit_confidence",
    "rank", "rank_confidence",
    "detected_confidence",
)


class PokerPredictorCommand(AbstractCommand):

    def __init__(self, poker_pipeline: AbstractPipeline) -> None:
        self.poker_pipeline = poker_pipeline

    @click.command("poker-predictor", cls=BoundCommand)
    @click.option("--workdir", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path), help="要辨識的圖片目錄（只讀第一層）")
    @click.option("--threads", type=click.IntRange(min=1), default=4, show_default=True, help="同時辨識的執行緒數量")
    def handle(self, workdir: Path, threads: int) -> None:
        """辨識 --workdir 目錄下所有圖片中的撲克牌"""
        l_images = sorted(p for p in workdir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES)
        if not l_images:
            raise click.ClickException(str(workdir) + " 底下沒有圖片（" + ", ".join(sorted(IMAGE_SUFFIXES)) + "）")

        click.secho("========== 使用模型 ==========", bold=True)
        for label, o_model in (
            ("偵測 card", self.poker_pipeline.poker_card_detector),
            ("分類 card", self.poker_pipeline.poker_card_classifier),
            ("分類 rank", self.poker_pipeline.poker_rank_classifier),
            ("分類 suit", self.poker_pipeline.poker_suit_classifier),
        ):
            click.echo("{}: {} (thres={})".format(label, o_model.model_dir, o_model.conf_threshold))

        f_started = time.perf_counter()

        # map 依輸入順序回傳結果，所以輸出順序跟檔名排序一致；任一張失敗會在迭代到它時拋出
        with ThreadPoolExecutor(max_workers=threads) as o_thread_pool_executor:
            l_results = list(o_thread_pool_executor.map(self.predict, l_images))

        f_elapsed = time.perf_counter() - f_started

        for image, l_dicts in zip(l_images, l_results):
            name = image.name
            # click.secho(name + "：共偵測到 " + str(len(l_dicts)) + " 張牌", bold=True)
            for i, d in enumerate(l_dicts, 1):
                line = "  #{} {} ({:.2f}) box=({},{},{},{})".format(i, d["name"], d["confidence"], d["x1"], d["y1"], d["x2"], d["y2"])
                if d["suit"] != "-" or d["rank"] != "-":
                    line += " 花色={} ({:.2f}) 點數={} ({:.2f})".format(d["suit"], d["suit_confidence"], d["rank"], d["rank_confidence"])
                # click.echo(line)

        click.secho("========== 報告 ==========", bold=True)
        click.echo("OpenVINO: {} (device={}, mode={})".format(openvino.__version__, bootstrap.config("openvino.device"), bootstrap.config("openvino.mode", "eager")))
        click.echo("線程數量: " + str(threads))
        click.echo("照片數量: " + str(len(l_images)))
        click.echo("總共時間: {:.1f} ms".format(f_elapsed * 1000))

    def predict(self, image: Path) -> list[dict]:
        f_started = time.perf_counter()
        frame_bgr = cv2.imread(str(image))
        if frame_bgr is None:
            raise click.ClickException("無法讀取圖片 " + str(image))
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        l_results = self.poker_pipeline.run(frame_rgb)
        l_dicts = [
            {k: (v if isinstance(v, (str, int)) else float(v)) for k, v in zip(RESULT_KEYS, t_result)}
            for t_result in l_results
        ]

        click.echo("{} 執行時間 {:.1f} ms".format(image.name, (time.perf_counter() - f_started) * 1000))
        return l_dicts
