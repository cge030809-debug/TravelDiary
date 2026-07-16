"""유사사진 묶기. (소유: 4번 사진 분석·선별)

거의 같은 장면의 연속 촬영을 한 그룹으로 묶어, 그룹당 1장만 대표로 남깁니다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PIL import Image

from ..models import Photo

_HASH_SIZE = 8
_MAX_HAMMING = 10


def group(photos: list[Photo], paths: dict[str, Path]) -> list[Photo]:
    """유사한 사진에 같은 group_id 를 부여."""
    hashes: dict[str, int | None] = {p.photo_id: _average_hash(paths.get(p.photo_id)) for p in photos}
    reps: list[tuple[str, int]] = []
    next_group = 0

    for p in photos:
        h = hashes[p.photo_id]
        if h is None:
            p.group_id = f"g{next_group}"
            next_group += 1
            continue

        matched = None
        for gid, rep_hash in reps:
            if _hamming(h, rep_hash) <= _MAX_HAMMING:
                matched = gid
                break

        if matched is None:
            gid = f"g{next_group}"
            next_group += 1
            reps.append((gid, h))
            p.group_id = gid
        else:
            p.group_id = matched

    return photos


def _average_hash(path: Optional[Path]) -> Optional[int]:
    if path is None:
        return None
    try:
        with Image.open(path) as img:
            small = img.convert("L").resize((_HASH_SIZE, _HASH_SIZE), Image.Resampling.LANCZOS)
        bits = 0
        pixels = list(small.getdata())
        avg = sum(pixels) / len(pixels)
        for px in pixels:
            bits = (bits << 1) | (1 if px >= avg else 0)
        return bits
    except Exception:
        return None


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")
