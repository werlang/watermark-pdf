"""Focused tests for CLI parsing and Ghostscript compression wiring."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.modules.setdefault(
    "pypdf",
    types.SimpleNamespace(PdfReader=object, PdfWriter=object),
)
sys.modules.setdefault(
    "reportlab.lib.colors",
    types.SimpleNamespace(Color=object),
)
sys.modules.setdefault(
    "reportlab.lib.utils",
    types.SimpleNamespace(ImageReader=object),
)
sys.modules.setdefault(
    "reportlab.pdfgen",
    types.SimpleNamespace(canvas=types.SimpleNamespace(Canvas=object)),
)

import watermark_pdf


class ParseArgsTests(unittest.TestCase):
    """Exercise the CLI contract around compression options."""

    def test_compression_quality_defaults_to_medium(self) -> None:
        """The compression preset should be predictable when the flag is used."""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_pdf = Path(temp_dir) / "input.pdf"
            output_pdf = Path(temp_dir) / "output.pdf"
            input_pdf.write_bytes(b"%PDF-1.4\n")

            args = watermark_pdf.parse_args(
                [str(input_pdf), str(output_pdf), "--compress"]
            )

        self.assertTrue(args.compress)
        self.assertEqual(args.compression_quality, "medium")

    def test_compression_quality_can_be_overridden(self) -> None:
        """Users should be able to choose a more aggressive preset."""

        with tempfile.TemporaryDirectory() as temp_dir:
            input_pdf = Path(temp_dir) / "input.pdf"
            output_pdf = Path(temp_dir) / "output.pdf"
            input_pdf.write_bytes(b"%PDF-1.4\n")

            args = watermark_pdf.parse_args(
                [
                    str(input_pdf),
                    str(output_pdf),
                    "--compress",
                    "--compression-quality",
                    "low",
                ]
            )

        self.assertEqual(args.compression_quality, "low")


class CompressPdfTests(unittest.TestCase):
    """Verify the Ghostscript invocation used for output-size reduction."""

    @patch("watermark_pdf.subprocess.run")
    @patch("watermark_pdf.shutil.which", return_value="/usr/bin/gs")
    def test_compress_pdf_uses_selected_quality_preset(
        self,
        _which_mock,
        run_mock,
    ) -> None:
        """The Ghostscript command should reflect the requested quality level."""

        watermark_pdf.compress_pdf(
            Path("/tmp/input.pdf"),
            Path("/tmp/output.pdf"),
            "high",
        )

        run_mock.assert_called_once_with(
            [
                "/usr/bin/gs",
                "-sDEVICE=pdfwrite",
                "-dCompatibilityLevel=1.4",
                "-dNOPAUSE",
                "-dQUIET",
                "-dBATCH",
                "-dPDFSETTINGS=/printer",
                "-sOutputFile=/tmp/output.pdf",
                "/tmp/input.pdf",
            ],
            check=True,
        )

    @patch("watermark_pdf.shutil.which", return_value=None)
    def test_compress_pdf_requires_ghostscript(self, _which_mock) -> None:
        """A missing optimizer binary should fail with a clear message."""

        with self.assertRaisesRegex(RuntimeError, "Ghostscript is required"):
            watermark_pdf.compress_pdf(
                Path("/tmp/input.pdf"),
                Path("/tmp/output.pdf"),
                "medium",
            )


if __name__ == "__main__":
    unittest.main()
