from pathlib import Path

from PIL import Image

from backend.models import Photo
from backend.services.dedupe import group
from backend.services.quality import score
from backend.services.selector import select


def _make_image(path: Path, color: tuple[int, int, int], size=(1600, 1200)) -> None:
    img = Image.new("RGB", size, color=color)
    img.save(path)


def test_score_populates_quality_fields(tmp_path: Path):
    path = tmp_path / "photo_a.jpeg"
    _make_image(path, (180, 140, 100))
    photo = Photo(photo_id="p1", filename=path.name)

    scored = score(photo, path)

    assert scored.quality_score is not None
    assert scored.sharpness_score is not None
    assert scored.resolution_score is not None
    assert scored.exposure_score is not None
    assert scored.composition_score is not None


def test_selector_keeps_top_photo_per_group(tmp_path: Path):
    path1 = tmp_path / "a.jpeg"
    path2 = tmp_path / "b.jpeg"
    _make_image(path1, (120, 120, 120))
    _make_image(path2, (210, 210, 210))

    photos = [
        score(Photo(photo_id="p1", filename=path1.name), path1),
        score(Photo(photo_id="p2", filename=path2.name), path2),
    ]

    for p in photos:
        p.group_id = "g1"

    selected = select(photos, max_count=1)

    assert len(selected) == 1
    assert selected[0].photo_id in {"p1", "p2"}


def test_dedupe_groups_identical_images(tmp_path: Path):
    path1 = tmp_path / "a.jpeg"
    path2 = tmp_path / "b.jpeg"
    _make_image(path1, (50, 60, 70))
    _make_image(path2, (50, 60, 70))

    photos = [
        Photo(photo_id="p1", filename=path1.name),
        Photo(photo_id="p2", filename=path2.name),
    ]
    grouped = group(photos, {"p1": path1, "p2": path2})

    assert grouped[0].group_id == grouped[1].group_id
