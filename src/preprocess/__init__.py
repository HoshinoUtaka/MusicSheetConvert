"""Image / PDF preprocessing: resize, binarize, denoise. Prepares sheet images for OMR."""
from __future__ import annotations

from pathlib import Path
from typing import Union

import cv2
from pdf2image import convert_from_path


PathLike = Union[str, Path]


def pdf_to_images(pdf_path: PathLike, out_dir: PathLike,
                  dpi: int = 300) -> list[Path]:
    """Convert every page of a PDF to a PNG image.

    Returns:
        A list of the actual PNG paths written, in page order.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(str(pdf_path), dpi=dpi)
    out_paths: list[Path] = []
    for idx, img in enumerate(pages, start=1):
        p = out_dir / f"{pdf_path.stem}_p{idx:03d}.png"
        img.save(p, "PNG")
        out_paths.append(p)
    return out_paths


def preprocess_image(img_path: PathLike,
                     out_path: PathLike | None = None,
                     max_side: int = 2400) -> Path:
    """Preprocess a single image: grayscale -> adaptive threshold -> optional resize.

    Args:
        img_path: input image path.
        out_path: output path. Defaults to ``<stem>_proc.png`` next to the input.
        max_side: longest-side cap. Larger images are scaled down proportionally.
    """
    img_path = Path(img_path)
    out_path = Path(out_path) if out_path else img_path.with_name(
        img_path.stem + "_proc.png"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Failed to read image: {img_path}")

    h, w = img.shape[:2]
    if max(h, w) > max_side:
        scale = max_side / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Adaptive thresholding handles uneven illumination on sheet scans better
    # than a global threshold.
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.adaptiveThreshold_GAUSSIAN_C if False else cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    # Light denoise.
    binary = cv2.medianBlur(binary, 3)
    cv2.imwrite(str(out_path), binary)
    return out_path
