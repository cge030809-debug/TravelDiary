"""EXIF 촬영시간·GPS 추출. (소유: 4번 사진 분석·선별)

파이프라인 첫 단계: 원본 파일에서 메타데이터를 뽑아 Photo 를 채웁니다.
파일이 이미지가 아니거나 EXIF 가 없어도 예외 없이 통과합니다.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.Image import Exif
from PIL.ImageOps import exif_transpose

from ..models import Photo

_EXIF_DATETIME_ORIGINAL = 0x9003
_EXIF_DATETIME_DIGITIZED = 0x9004
_EXIF_DATETIME = 0x0132
_EXIF_GPS_INFO = 0x8825


def extract(path: Path) -> Photo:
    """사진 파일 1장 -> Photo(메타데이터)."""
    photo = Photo(photo_id=uuid.uuid4().hex, filename=path.name)

    try:
        with Image.open(path) as img:
            normalized = exif_transpose(img)
            photo.width, photo.height = normalized.size
            exif = normalized.getexif()
            photo.taken_at = _read_taken_at(exif)
            photo.lat, photo.lng = _read_gps(exif)
    except Exception:
        # 이미지가 아니거나 손상된 파일 → 파일명만 가진 채로 통과
        pass

    return photo


def _read_taken_at(exif: Exif) -> datetime | None:
    try:
        for tag in (_EXIF_DATETIME_ORIGINAL, _EXIF_DATETIME_DIGITIZED, _EXIF_DATETIME):
            raw = exif.get(tag)
            if raw:
                return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    return None


def _read_gps(exif: Exif) -> tuple[float | None, float | None]:
    try:
        gps = exif.get_ifd(_EXIF_GPS_INFO)
        lat = _to_decimal(gps.get(2), gps.get(1))
        lng = _to_decimal(gps.get(4), gps.get(3))
        return lat, lng
    except Exception:
        return None, None


def _to_decimal(dms, ref) -> float | None:
    """(도, 분, 초) + 방향(N/S/E/W) -> 십진수 좌표."""
    if not dms or ref is None:
        return None
    try:
        deg, minutes, sec = (float(x) for x in dms)
        value = deg + minutes / 60 + sec / 3600
        if str(ref).upper() in ("S", "W"):
            value = -value
        return value
    except Exception:
        return None
