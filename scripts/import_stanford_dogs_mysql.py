from __future__ import annotations

import argparse
import mysql.connector
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from scipy.io import loadmat


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Stanford Dogs metadata into MySQL stanford_dogs database."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help="Root folder that contains extracted Annotation/ and Images/ directories.",
    )
    parser.add_argument(
        "--lists-root",
        type=Path,
        required=True,
        help="Folder that contains train_list.mat and test_list.mat.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="MySQL host.",
    )
    parser.add_argument(
        "--user",
        type=str,
        default="root",
        help="MySQL user.",
    )
    parser.add_argument(
        "--password",
        type=str,
        default="",
        help="MySQL password.",
    )
    parser.add_argument(
        "--database",
        type=str,
        default="stanford_dogs",
        help="MySQL database name.",
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


def detect_annotation_root(dataset_root: Path) -> Path:
    candidates = [
        dataset_root / "Annotation",
        dataset_root / "annotation",
        dataset_root / "Annotations",
        dataset_root / "annotations",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find Annotation folder under --dataset-root. "
        "Expected one of: Annotation, annotation, Annotations, annotations."
    )


def annotation_candidates(annotation_root: Path, rel_path: str) -> list[Path]:
    without_ext = str(Path(rel_path).with_suffix(""))
    return [
        annotation_root / without_ext,
        annotation_root / f"{without_ext}.xml",
        annotation_root / rel_path,
        annotation_root / f"{rel_path}.xml",
    ]


def parse_single_annotation(annotation_path: Path) -> tuple[list[tuple[int, int, int, int]], int | None, int | None]:
    root = ET.parse(annotation_path).getroot()
    boxes: list[tuple[int, int, int, int]] = []
    
    width = None
    height = None
    
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
    
    try:
        size = root.find("size")
        if size is not None:
            width_text = size.findtext("width")
            height_text = size.findtext("height")
            if width_text and height_text:
                width = int(float(width_text))
                height = int(float(height_text))
    except (ValueError, TypeError):
        pass
    
    return boxes, width, height


def main() -> None:
    args = parse_args()

    train_mat = args.lists_root / "train_list.mat"
    test_mat = args.lists_root / "test_list.mat"
    if not train_mat.exists() or not test_mat.exists():
        raise FileNotFoundError(
            "Could not find train_list.mat and test_list.mat in --lists-root."
        )

    annotation_root = detect_annotation_root(args.dataset_root)

    conn = mysql.connector.connect(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database
    )
    cursor = conn.cursor()

    try:
        breed_count = 0
        image_count = 0
        bbox_count = 0

        # Insert breeds and images from train set
        for rel_path, label in iter_mat_list(train_mat):
            synset, breed_name = parse_breed(rel_path)
            file_name = Path(rel_path).name

            # Insert or ignore breed
            cursor.execute(
                """
                INSERT IGNORE INTO breeds (class_label, synset, breed_name)
                VALUES (%s, %s, %s)
                """,
                (label, synset, breed_name),
            )
            if cursor.rowcount > 0:
                breed_count += 1

            # Get breed_id
            cursor.execute("SELECT breed_id FROM breeds WHERE synset = %s", (synset,))
            breed_id_row = cursor.fetchone()
            if not breed_id_row:
                continue
            breed_id = breed_id_row[0]

            # Insert or ignore image
            cursor.execute(
                """
                INSERT IGNORE INTO images (breed_id, relative_path, file_name)
                VALUES (%s, %s, %s)
                """,
                (breed_id, rel_path, file_name),
            )
            if cursor.rowcount > 0:
                image_count += 1

            # Get image_id
            cursor.execute("SELECT image_id FROM images WHERE relative_path = %s", (rel_path,))
            image_id_row = cursor.fetchone()
            if not image_id_row:
                continue
            image_id = image_id_row[0]

            # Insert dataset_split
            cursor.execute(
                """
                INSERT IGNORE INTO dataset_split (image_id, split, list_label)
                VALUES (%s, %s, %s)
                """,
                (image_id, "train", label),
            )

        # Insert images from test set
        for rel_path, label in iter_mat_list(test_mat):
            synset, breed_name = parse_breed(rel_path)
            file_name = Path(rel_path).name

            # Get breed_id (breed should already exist)
            cursor.execute("SELECT breed_id FROM breeds WHERE synset = %s", (synset,))
            breed_id_row = cursor.fetchone()
            if not breed_id_row:
                continue
            breed_id = breed_id_row[0]

            # Insert or ignore image
            cursor.execute(
                """
                INSERT IGNORE INTO images (breed_id, relative_path, file_name)
                VALUES (%s, %s, %s)
                """,
                (breed_id, rel_path, file_name),
            )
            if cursor.rowcount > 0:
                image_count += 1

            # Get image_id
            cursor.execute("SELECT image_id FROM images WHERE relative_path = %s", (rel_path,))
            image_id_row = cursor.fetchone()
            if not image_id_row:
                continue
            image_id = image_id_row[0]

            # Insert dataset_split
            cursor.execute(
                """
                INSERT IGNORE INTO dataset_split (image_id, split, list_label)
                VALUES (%s, %s, %s)
                """,
                (image_id, "test", label),
            )

        # Import annotations
        cursor.execute("SELECT image_id, relative_path FROM images")
        image_rows = cursor.fetchall()

        for image_id, rel_path in image_rows:
            ann_path = None
            for candidate in annotation_candidates(annotation_root, rel_path):
                if candidate.exists() and candidate.is_file():
                    ann_path = candidate
                    break
            if ann_path is None:
                continue

            boxes, width, height = parse_single_annotation(ann_path)

            for xmin, ymin, xmax, ymax in boxes:
                cursor.execute(
                    """
                    INSERT INTO bounding_boxes (image_id, xmin, ymin, xmax, ymax)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (image_id, xmin, ymin, xmax, ymax),
                )
                bbox_count += 1

            if width is not None and height is not None:
                cursor.execute(
                    "UPDATE images SET width = %s, height = %s WHERE image_id = %s",
                    (width, height, image_id),
                )

        conn.commit()

        print(f"Import complete. Breeds: {breed_count}, Images: {image_count}, BBoxes: {bbox_count}")

    except Exception as e:
        conn.rollback()
        print(f"Import failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
