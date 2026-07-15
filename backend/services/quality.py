"""흐림·노출·해상도 품질 평가. (소유: 4번 사진 분석·선별)

각 사진에 0~1 품질점수를 매겨 대표사진 선별의 근거로 씁니다.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from ..models import Photo

_BLUR_THRESHOLD = 35.0
_MIN_MEGAPIXELS = 0.75
_PREFERRED_MEGAPIXELS = 4.0
_MIN_SHORT_EDGE = 720
_PREFERRED_SHORT_EDGE = 1600


def _scale(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _laplacian_variance(gray: np.ndarray) -> float:
    if gray.ndim != 2 or gray.shape[0] < 3 or gray.shape[1] < 3:
        return 0.0
    center = gray[1:-1, 1:-1]
    laplacian = (
        gray[:-2, 1:-1]
        + gray[2:, 1:-1]
        + gray[1:-1, :-2]
        + gray[1:-1, 2:]
        - (4 * center)
    )
    return float(np.var(laplacian))


def score(photo: Photo, path: Path) -> Photo:
    """Photo 에 quality_score(0~1) 를 채워 반환."""
    try:
        with Image.open(path) as img:
            normalized = ImageOps.exif_transpose(img)
            width, height = normalized.size
            gray_img = normalized.convert("L")
            gray_img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            gray = np.asarray(gray_img, dtype=np.float32)

            sharpness_raw = _laplacian_variance(gray)
            sharpness_score = _scale(math.log1p(sharpness_raw), math.log1p(20), math.log1p(350))

            megapixels = (width * height) / 1_000_000
            short_edge = min(width, height)
            megapixel_score = _scale(megapixels, _MIN_MEGAPIXELS, _PREFERRED_MEGAPIXELS)
            short_edge_score = _scale(short_edge, _MIN_SHORT_EDGE, _PREFERRED_SHORT_EDGE)
            resolution_score = (0.6 * megapixel_score) + (0.4 * short_edge_score)

            brightness = float(np.mean(gray)) / 255.0
            darkness_ratio = float(np.mean(gray <= 5))
            highlight_ratio = float(np.mean(gray >= 250))
            brightness_score = 1 - min(1.0, abs(brightness - 0.5) / 0.5)
            clipping_score = 1 - min(1.0, (darkness_ratio + highlight_ratio) / 0.35)
            exposure_score = (0.6 * brightness_score) + (0.4 * clipping_score)

            total_score = (0.6 * sharpness_score) + (0.3 * resolution_score) + (0.1 * exposure_score)
            photo.quality_score = round(total_score, 3)
    except Exception:
        photo.quality_score = 0.5   # 판단 불가 → 중립
    return photo
