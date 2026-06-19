"""Add a text or image watermark to one PDF or many PDFs.

The script creates a transparent overlay for each page, draws the watermark
content onto that overlay, and merges it into the source document without
modifying the original file.
"""

from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

COMPRESSION_PRESETS = {
    "low": "/screen",
    "medium": "/ebook",
    "high": "/printer",
    "max": "/prepress",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Add a watermark to PDF files.")
    parser.add_argument(
        "input_path",
        type=Path,
        help="Path to a PDF file or a directory containing PDFs",
    )
    parser.add_argument(
        "output_path",
        type=Path,
        help="Output PDF path or output directory when processing a directory",
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--text",
        help="Watermark text to draw on every page",
    )
    source_group.add_argument(
        "--image",
        type=Path,
        help="Image file to use as the watermark instead of text",
    )
    parser.add_argument(
        "--font-size",
        type=float,
        default=54,
        help="Watermark font size for text watermarks",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=45,
        help="Watermark rotation angle in degrees",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        default=0.18,
        help="Watermark opacity from 0.0 to 1.0",
    )
    parser.add_argument(
        "--color",
        default="0.2,0.2,0.2",
        help="RGB color as comma-separated floats between 0 and 1 for text watermarks",
    )
    parser.add_argument(
        "--image-scale",
        type=float,
        default=0.45,
        help="Relative size of an image watermark compared to the page width",
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Run an extra Ghostscript optimization pass to reduce the final PDF size",
    )
    parser.add_argument(
        "--compression-quality",
        choices=tuple(COMPRESSION_PRESETS),
        default="medium",
        help="Quality preset for --compress: low, medium, high, or max",
    )
    args = parser.parse_args(argv)

    if args.text is None and args.image is None:
        args.text = "CONFIDENTIAL"
    if args.text is not None and args.image is not None:
        parser.error("choose only one of --text or --image")
    if args.image is not None and not args.image.is_file():
        parser.error(f"watermark image does not exist: {args.image}")
    if not args.input_path.exists():
        parser.error(f"input path does not exist: {args.input_path}")
    if args.input_path.is_file() and args.input_path.suffix.lower() != ".pdf":
        parser.error("input file must be a PDF")
    return args


def parse_rgb(value: str) -> tuple[float, float, float]:
    """Parse an RGB triple from the command line."""

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise ValueError("color must contain exactly three comma-separated values")

    rgb = tuple(float(part) for part in parts)
    if any(component < 0.0 or component > 1.0 for component in rgb):
        raise ValueError("color components must be between 0 and 1")
    return rgb


def create_text_overlay(
    page_width: float,
    page_height: float,
    text: str,
    font_size: float,
    angle: float,
    opacity: float,
    color: tuple[float, float, float],
) -> bytes:
    """Render a single-page PDF containing a text watermark overlay."""

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.saveState()
    pdf.translate(page_width / 2, page_height / 2)
    pdf.rotate(angle)
    pdf.setFillColor(Color(color[0], color[1], color[2], alpha=opacity))
    pdf.setFont("Helvetica-Bold", font_size)
    pdf.drawCentredString(0, 0, text)
    pdf.restoreState()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def create_image_overlay(
    page_width: float,
    page_height: float,
    image_path: Path,
    angle: float,
    opacity: float,
    image_scale: float,
) -> bytes:
    """Render a single-page PDF containing an image watermark overlay."""

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    pdf.saveState()
    pdf.translate(page_width / 2, page_height / 2)
    pdf.rotate(angle)
    pdf.setFillAlpha(opacity)
    pdf.setStrokeAlpha(opacity)

    image = ImageReader(str(image_path))
    image_width, image_height = image.getSize()
    max_width = page_width * image_scale
    if image_width == 0 or image_height == 0:
        raise ValueError(f"invalid image watermark: {image_path}")
    scale = max_width / image_width
    draw_width = image_width * scale
    draw_height = image_height * scale
    pdf.drawImage(
        image,
        -draw_width / 2,
        -draw_height / 2,
        width=draw_width,
        height=draw_height,
        mask="auto",
    )
    pdf.restoreState()
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def build_overlay(
    page_width: float,
    page_height: float,
    text: str | None,
    image: Path | None,
    font_size: float,
    angle: float,
    opacity: float,
    color: tuple[float, float, float],
    image_scale: float,
) -> bytes:
    """Create the watermark overlay for a single page."""

    if text is not None:
        return create_text_overlay(
            page_width,
            page_height,
            text,
            font_size,
            angle,
            opacity,
            color,
        )

    if image is None:
        raise ValueError("an image watermark requires an image path")

    return create_image_overlay(
        page_width,
        page_height,
        image,
        angle,
        opacity,
        image_scale,
    )


def add_watermark(
    input_pdf: Path,
    output_pdf: Path,
    text: str | None,
    image: Path | None,
    font_size: float,
    angle: float,
    opacity: float,
    color: tuple[float, float, float],
    image_scale: float,
) -> None:
    """Apply the watermark to every page in the input PDF."""

    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()

    for page in reader.pages:
        watermark_pdf = PdfReader(
            io.BytesIO(
                build_overlay(
                    float(page.mediabox.width),
                    float(page.mediabox.height),
                    text,
                    image,
                    font_size,
                    angle,
                    opacity,
                    color,
                    image_scale,
                )
            )
        )
        watermark_page = watermark_pdf.pages[0]
        page.merge_page(watermark_page)
        writer.add_page(page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as fh:
        writer.write(fh)


def compress_pdf(
    input_pdf: Path,
    output_pdf: Path,
    quality: str,
) -> None:
    """Optimize a PDF with Ghostscript using a caller-selected quality preset."""

    ghostscript = shutil.which("gs")
    if ghostscript is None:
        raise RuntimeError(
            "Ghostscript is required for --compress. Rebuild the Docker image after updating the repo."
        )

    preset = COMPRESSION_PRESETS[quality]
    command = [
        ghostscript,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-dPDFSETTINGS={preset}",
        f"-sOutputFile={output_pdf}",
        str(input_pdf),
    ]
    subprocess.run(command, check=True)


def iter_input_pdfs(input_path: Path):
    """Yield PDFs to process from a file or directory."""

    if input_path.is_file():
        yield input_path, input_path.name
        return

    for pdf_path in sorted(input_path.rglob("*.pdf")):
        relative_name = pdf_path.relative_to(input_path)
        yield pdf_path, relative_name


def process_path(
    input_path: Path,
    output_path: Path,
    text: str | None,
    image: Path | None,
    font_size: float,
    angle: float,
    opacity: float,
    color: tuple[float, float, float],
    image_scale: float,
    compress: bool,
    compression_quality: str,
) -> None:
    """Process either one PDF or all PDFs under a directory."""

    for source_pdf, relative_name in iter_input_pdfs(input_path):
        destination_pdf = output_path if input_path.is_file() else output_path / relative_name
        destination_pdf.parent.mkdir(parents=True, exist_ok=True)

        if compress:
            # Write the watermarked PDF first, then let Ghostscript trade image
            # quality for size using the requested preset.
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                temp_output = Path(tmp_file.name)
            try:
                add_watermark(
                    source_pdf,
                    temp_output,
                    text,
                    image,
                    font_size,
                    angle,
                    opacity,
                    color,
                    image_scale,
                )
                compress_pdf(temp_output, destination_pdf, compression_quality)
            finally:
                temp_output.unlink(missing_ok=True)
            continue

        add_watermark(
            source_pdf,
            destination_pdf,
            text,
            image,
            font_size,
            angle,
            opacity,
            color,
            image_scale,
        )


def main() -> None:
    """CLI entry point."""

    args = parse_args()
    if args.input_path.is_dir():
        args.output_path.mkdir(parents=True, exist_ok=True)
    elif args.output_path.exists() and args.output_path.is_dir():
        raise IsADirectoryError("output_path must be a file when input_path is a PDF")

    process_path(
        args.input_path,
        args.output_path,
        args.text,
        args.image,
        args.font_size,
        args.angle,
        args.opacity,
        parse_rgb(args.color),
        args.image_scale,
        args.compress,
        args.compression_quality,
    )


if __name__ == "__main__":
    main()
