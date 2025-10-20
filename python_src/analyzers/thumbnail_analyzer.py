"""サムネイル品質評価

画像の解像度、文字量、背景処理などをスコア化して
サムネイル品質を0-100点で評価
"""

import io
from typing import Optional, Dict, Any

import cv2
import numpy as np
import requests
from PIL import Image
from pydantic import BaseModel, Field


class ThumbnailScore(BaseModel):
    """サムネイル品質スコア"""

    total_score: float = Field(description="総合スコア (0-100)")
    resolution_score: float = Field(description="解像度スコア (0-30)")
    text_density_score: float = Field(description="文字密度スコア (0-25)")
    background_score: float = Field(description="背景処理スコア (0-25)")
    brightness_score: float = Field(description="明るさスコア (0-20)")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細データ")


class ThumbnailAnalyzer:
    """サムネイル品質分析"""

    # スコアリング基準
    MIN_RESOLUTION = (300, 300)  # 最低解像度
    OPTIMAL_RESOLUTION = (800, 800)  # 最適解像度
    TARGET_BRIGHTNESS = 128  # 目標明度(0-255)
    OPTIMAL_TEXT_RATIO = 0.15  # 最適な文字領域比率

    def analyze_from_url(self, image_url: str) -> Optional[ThumbnailScore]:
        """URLから画像を取得して品質評価

        Args:
            image_url: 画像URL

        Returns:
            品質スコア、取得失敗時はNone
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_bytes = response.content

            return self.analyze_from_bytes(image_bytes)

        except requests.RequestException as e:
            print(f"画像取得エラー ({image_url}): {e}")
            return None

    def analyze_from_bytes(self, image_bytes: bytes) -> ThumbnailScore:
        """バイトデータから画像品質評価

        Args:
            image_bytes: 画像バイナリ

        Returns:
            品質スコア
        """
        # PILで画像を開く
        pil_image = Image.open(io.BytesIO(image_bytes))

        # OpenCV用にNumpy配列に変換
        np_image = np.array(pil_image.convert("RGB"))
        cv_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)

        # 各スコアを計算
        resolution_score = self._score_resolution(pil_image)
        text_density_score = self._score_text_density(cv_image)
        background_score = self._score_background(cv_image)
        brightness_score = self._score_brightness(cv_image)

        total_score = (
            resolution_score + text_density_score + background_score + brightness_score
        )

        return ThumbnailScore(
            total_score=round(total_score, 2),
            resolution_score=round(resolution_score, 2),
            text_density_score=round(text_density_score, 2),
            background_score=round(background_score, 2),
            brightness_score=round(brightness_score, 2),
            details={
                "resolution": pil_image.size,
                "format": pil_image.format,
            },
        )

    def _score_resolution(self, image: Image.Image) -> float:
        """解像度スコア (0-30点)

        Args:
            image: PIL画像

        Returns:
            スコア
        """
        width, height = image.size
        resolution = min(width, height)

        # 300px未満: 0点
        # 300px: 10点
        # 800px以上: 30点
        if resolution < self.MIN_RESOLUTION[0]:
            return 0.0
        elif resolution >= self.OPTIMAL_RESOLUTION[0]:
            return 30.0
        else:
            # 線形補間
            score = 10 + ((resolution - 300) / 500) * 20
            return score

    def _score_text_density(self, image: np.ndarray) -> float:
        """文字密度スコア (0-25点)

        テキスト領域の割合を推定。適度な文字量が高スコア。

        Args:
            image: OpenCV画像(BGR)

        Returns:
            スコア
        """
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # エッジ検出でテキスト領域を推定
        edges = cv2.Canny(gray, 50, 150)

        # エッジ画素の割合
        total_pixels = edges.size
        edge_pixels = np.count_nonzero(edges)
        edge_ratio = edge_pixels / total_pixels

        # 最適な文字量は10-20%程度
        # 0-5%: 文字が少なすぎる (10点)
        # 10-20%: 最適 (25点)
        # 30%以上: 文字が多すぎる (10点)

        if edge_ratio < 0.05:
            score = edge_ratio * 200  # 0-10点
        elif edge_ratio <= 0.20:
            score = 10 + ((edge_ratio - 0.05) / 0.15) * 15  # 10-25点
        else:
            score = max(10, 25 - ((edge_ratio - 0.20) * 50))  # 25点から減点

        return min(25.0, max(0.0, score))

    def _score_background(self, image: np.ndarray) -> float:
        """背景処理スコア (0-25点)

        白抜き・単色背景などの整理された背景が高スコア。

        Args:
            image: OpenCV画像(BGR)

        Returns:
            スコア
        """
        # 画像を9つのブロックに分割し、周辺ブロックの色の均一性を評価
        height, width = image.shape[:2]
        block_h, block_w = height // 3, width // 3

        # 周辺8ブロックの平均色を取得
        peripheral_blocks = [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 2),
            (2, 0),
            (2, 1),
            (2, 2),
        ]

        block_colors = []
        for i, j in peripheral_blocks:
            block = image[i * block_h : (i + 1) * block_h, j * block_w : (j + 1) * block_w]
            avg_color = np.mean(block, axis=(0, 1))
            block_colors.append(avg_color)

        # 周辺ブロック間の色の標準偏差
        std_dev = np.std(block_colors, axis=0).mean()

        # 標準偏差が小さいほど背景が均一 → 高スコア
        # std_dev < 10: 25点
        # std_dev = 50: 12.5点
        # std_dev > 100: 0点
        if std_dev < 10:
            score = 25.0
        elif std_dev < 100:
            score = 25 - ((std_dev - 10) / 90) * 25
        else:
            score = 0.0

        return score

    def _score_brightness(self, image: np.ndarray) -> float:
        """明るさスコア (0-20点)

        適度な明るさ(128付近)が高スコア。

        Args:
            image: OpenCV画像(BGR)

        Returns:
            スコア
        """
        # グレースケール変換
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 平均明度
        avg_brightness = np.mean(gray)

        # 目標明度128からの差分
        diff = abs(avg_brightness - self.TARGET_BRIGHTNESS)

        # 差分が小さいほど高スコア
        # diff = 0: 20点
        # diff = 64: 10点
        # diff = 128: 0点
        if diff <= 64:
            score = 20 - (diff / 64) * 10
        else:
            score = max(0, 10 - ((diff - 64) / 64) * 10)

        return score
