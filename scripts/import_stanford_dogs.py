from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from scipy.io import loadmat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Stanford Dogs metadata into a SQLite database."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help="Root folder that contains extracted images/ and annotation/ directories.",
    )
    parser.add_argument(
        "--lists-root",
        type=Path,
        required=True,
        help="Folder that contains train_list.mat and test_list.mat.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("stanford_dogs.db"),
        help="SQLite database output path.",
    )
    parser.add_argument(
        "--schema-path",
        type=Path,
        default=Path("sql/schema.sql"),
        help="Path to schema SQL file.",
    )
    return parser.parse_args()


def as_text(value) -> str:
    """Flatten MATLAB-loaded objects into a normalized path string."""
    while hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            if len(value) == 0:
                break
            value = value[0]
            continue
        except TypeError:
            break
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def as_int(value) -> int:
    while hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            if len(value) == 0:
                break
            value = value[0]
            continue
        except TypeError:
            break
    return int(value)


def parse_breed(relative_path: str) -> tuple[str, str]:
    folder_name = relative_path.split("/")[0]
    if "-" in folder_name:
        synset, breed_raw = folder_name.split("-", 1)
    else:
        synset = folder_name
        breed_raw = folder_name
    breed_name = breed_raw.replace("_", " ")
    return synset, breed_name


def iter_mat_list(mat_path: Path) -> Iterable[tuple[str, int]]:
    mat = loadmat(str(mat_path))
    file_list = mat["file_list"]
    labels = mat["labels"]

    for file_obj, label_obj in zip(file_list, labels):
        rel_path = as_text(file_obj).replace("\\", "/")
        label = as_int(label_obj)
        yield rel_path, label


def apply_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    conn.executescript(schema_path.read_text(encoding="utf-8"))


def upsert_image_with_split(
    conn: sqlite3.Connection,
    rel_path: str,
    label: int,
    split: str,
) -> None:
    synset, breed_name = parse_breed(rel_path)
    file_name = Path(rel_path).name

    conn.execute(
        """
        INSERT INTO breeds (class_label, synset, breed_name)
        VALUES (?, ?, ?)
        ON CONFLICT(synset) DO UPDATE SET
            class_label = excluded.class_label,
            breed_name = excluded.breed_name
        """,
        (label, synset, breed_name),
    )

    conn.execute(
        """
        INSERT INTO images (breed_id, relative_path, file_name)
        VALUES ((SELECT breed_id FROM breeds WHERE synset = ?), ?, ?)
        ON CONFLICT(relative_path) DO UPDATE SET
            breed_id = (SELECT breed_id FROM breeds WHERE synset = ?),
            file_name = excluded.file_name
        """,
        (synset, rel_path, file_name, synset),
    )

    conn.execute(
        """
        INSERT INTO dataset_split (image_id, split, list_label)
        VALUES ((SELECT image_id FROM images WHERE relative_path = ?), ?, ?)
        ON CONFLICT(image_id) DO UPDATE SET
            split = excluded.split,
            list_label = excluded.list_label
        """,
        (rel_path, split, label),
    )


def annotation_candidates(annotation_root: Path, rel_path: str) -> list[Path]:
    without_ext = str(Path(rel_path).with_suffix(""))
    return [
        annotation_root / without_ext,
        annotation_root / f"{without_ext}.xml",
        annotation_root / rel_path,
        annotation_root / f"{rel_path}.xml",
    ]


def parse_single_annotation(annotation_path: Path) -> list[tuple[int, int, int, int]]:
    root = ET.parse(annotation_path).getroot()
    boxes: list[tuple[int, int, int, int]] = []
    for obj in root.findall("object"):
        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue
        xmin = int(float(bndbox.findtext("xmin", "0")))
        ymin = int(float(bndbox.findtext("ymin", "0")))
        xmax = int(float(bndbox.findtext("xmax", "0")))
        ymax = int(float(bndbox.findtext("ymax", "0")))
        if xmax > xmin and ymax > ymin:
            boxes.append((xmin, ymin, xmax, ymax))
    return boxes


def detect_annotation_root(dataset_root: Path) -> Path:
    candidates = [
        dataset_root / "annotation",
        dataset_root / "annotations",
        dataset_root / "Annotation",
        dataset_root / "Annotations",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find annotation folder under --dataset-root. "
        "Expected one of: annotation, annotations, Annotation, Annotations."
    )


def import_annotations(conn: sqlite3.Connection, annotation_root: Path) -> int:
    inserted = 0
    rows = conn.execute("SELECT image_id, relative_path FROM images").fetchall()

    for image_id, rel_path in rows:
        ann_path = None
        for candidate in annotation_candidates(annotation_root, rel_path):
            if candidate.exists() and candidate.is_file():
                ann_path = candidate
                break
        if ann_path is None:
            continue

        boxes = parse_single_annotation(ann_path)
        for xmin, ymin, xmax, ymax in boxes:
            conn.execute(
                """
                INSERT INTO bounding_boxes (image_id, xmin, ymin, xmax, ymax)
                VALUES (?, ?, ?, ?, ?)
                """,
                (image_id, xmin, ymin, xmax, ymax),
            )
            inserted += 1

        try:
            tree = ET.parse(ann_path)
            size = tree.getroot().find("size")
            if size is not None:
                width_text = size.findtext("width")
                height_text = size.findtext("height")
                if width_text and height_text:
                    conn.execute(
                        "UPDATE images SET width = ?, height = ? WHERE image_id = ?",
                        (int(float(width_text)), int(float(height_text)), image_id),
                    )
        except ET.ParseError:
            continue

    return inserted


def main() -> None:
    args = parse_args()

    train_mat = args.lists_root / "train_list.mat"
    test_mat = args.lists_root / "test_list.mat"
    if not train_mat.exists() or not test_mat.exists():
        raise FileNotFoundError(
            "Could not find train_list.mat and test_list.mat in --lists-root."
        )

    annotation_root = detect_annotation_root(args.dataset_root)

    conn = sqlite3.connect(args.db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        apply_schema(conn, args.schema_path)

        for rel_path, label in iter_mat_list(train_mat):
            upsert_image_with_split(conn, rel_path, label, "train")

        for rel_path, label in iter_mat_list(test_mat):
            upsert_image_with_split(conn, rel_path, label, "test")

        bbox_count = import_annotations(conn, annotation_root)
        conn.commit()

        breed_count = conn.execute("SELECT COUNT(*) FROM breeds").fetchone()[0]
        image_count = conn.execute("SELECT COUNT(*) FROM images").fetchone()[0]

        print(f"Import complete. Breeds: {breed_count}, Images: {image_count}, BBoxes: {bbox_count}")
        print(f"Database created at: {args.db_path.resolve()}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
