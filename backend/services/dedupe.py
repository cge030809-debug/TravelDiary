"""사진 그룹핑. (소유: 4번 사진 분석·선별)

같은 "장소(스팟)"의 사진을 한 그룹으로 묶어 그룹당 1장만 대표로 남깁니다.
- GPS 가 있으면: 위치 근접(반경 기준)으로 묶음 → 같은 장소면 구도가 달라도 한 피드.
- GPS 가 없으면: 유사사진 해시(연속 촬영)로 묶음.
"""
from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from pathlib import Path
from typing import Optional

from PIL import Image

from ..models import Photo

_HASH_SIZE = 8
_MAX_HAMMING = 10
_SPOT_RADIUS_M = 150.0   # 이 반경 안의 사진은 "같은 장소"로 보고 한 그룹으로 묶음


def group(photos: list[Photo], paths: dict[str, Path]) -> list[Photo]:
    """같은 장소(또는 유사 연속샷) 사진에 같은 group_id 를 부여."""
    location_anchors: list[tuple[str, float, float]] = []  # (gid, lat, lng)
    hash_reps: list[tuple[str, int]] = []                  # (gid, hash)
    next_group = 0

    for p in photos:
        # 1) 위치가 있으면 근접한 기존 스팟에 합류, 없으면 새 스팟
        if p.lat is not None and p.lng is not None:
            matched = None
            for gid, alat, alng in location_anchors:
                if _haversine_m(p.lat, p.lng, alat, alng) <= _SPOT_RADIUS_M:
                    matched = gid
                    break
            if matched is None:
                gid = f"s{next_group}"
                next_group += 1
                location_anchors.append((gid, p.lat, p.lng))
                p.group_id = gid
            else:
                p.group_id = matched
            continue

        # 2) 위치가 없으면 유사사진 해시로 묶음
        h = _average_hash(paths.get(p.photo_id))
        if h is None:
            p.group_id = f"g{next_group}"
            next_group += 1
            continue
        matched = None
        for gid, rep_hash in hash_reps:
            if _hamming(h, rep_hash) <= _MAX_HAMMING:
                matched = gid
                break
        if matched is None:
            gid = f"g{next_group}"
            next_group += 1
            hash_reps.append((gid, h))
            p.group_id = gid
        else:
            p.group_id = matched

    return photos


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6_371_000
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * r * atan2(sqrt(h), sqrt(1 - h))


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
