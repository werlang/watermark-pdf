# watermark-pdf

CLI utility for applying a text or image watermark to PDF files through Docker Compose.

It supports:

- one input PDF to one output PDF
- one input directory to one output directory
- text or image watermarks

The source PDFs are left untouched. Watermarks are merged into new output files.

## Requirements

- Docker
- Docker Compose v2 (`docker compose`)

## Setup

Create a local `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Adjust the values in `.env` if needed:

```bash
WATERMARK_FILE=watermarks/wm-review.png
WATERMARK_ANGLE=35
WATERMARK_OPACITY=0.25
WATERMARK_SCALE=1
PDF_PATH=pdf
OUTPUT_PATH=output
```

## Quick Start

Build the image once:

```bash
docker compose build
```

Run the default compose command:

```bash
docker compose run --rm watermark-pdf
```

By default, the service reads values from `.env` and runs:

```bash
python3 /app/watermark_pdf.py pdf output --image watermarks/wm-review.png --angle 35 --opacity 0.25 --image-scale 1
```

## Manual

### 1. Build the container

```bash
docker compose build
```

This installs the Python dependencies from `requirements.txt` inside the image. You do not need to install `pypdf` or `reportlab` locally.

### 2. Run with the defaults from `.env`

```bash
docker compose run --rm watermark-pdf
```

This processes the PDF path in `PDF_PATH` and writes to `OUTPUT_PATH`.

### 3. Change the defaults through `.env`

Edit `.env` to change:

- `PDF_PATH`
- `OUTPUT_PATH`
- `WATERMARK_FILE`
- `WATERMARK_ANGLE`
- `WATERMARK_OPACITY`
- `WATERMARK_SCALE`

Then rerun:

```bash
docker compose run --rm watermark-pdf
```

### 4. Watermark a single PDF with text

```bash
docker compose run --rm watermark-pdf ./pdf/profs1.pdf ./output/profs1-confidential.pdf --text "CONFIDENTIAL"
```

### 5. Watermark a single PDF with an image

```bash
docker compose run --rm watermark-pdf ./pdf/turmas1.pdf ./output/turmas1-review.pdf --image ./watermarks/wm-review.png --angle 315 --opacity 0.25 --image-scale 0.45
```

### 5a. Compress the generated PDF

```bash
docker compose run --rm watermark-pdf ./pdf/turmas1.pdf ./output/turmas1-review.pdf --image ./watermarks/wm-review.png --compress --compression-quality medium
```

This writes the watermarked PDF first, then runs a Ghostscript optimization pass that can downsample and re-encode PDF content to shrink the final file.

### 6. Process an entire directory manually

```bash
docker compose run --rm watermark-pdf ./pdf ./output --text "INTERNAL"
```

When the input is a directory, the script:

- scans for `*.pdf` files recursively
- creates the output directory automatically
- preserves the input directory structure inside the output directory

## Usage

### Command format

```bash
docker compose run --rm watermark-pdf [INPUT OUTPUT [options]]
```

If `INPUT` and `OUTPUT` are omitted, the service uses the values from `.env` and the compose command defined in `compose.yaml`.

### Positional arguments

- `INPUT`: a PDF file or a directory containing PDFs
- `OUTPUT`: an output PDF file when `INPUT` is a file, or an output directory when `INPUT` is a directory

### Watermark source

Choose one:

- `--text "VALUE"`
- `--image /path/to/file.png`

If neither is provided, the default text watermark is:

```text
CONFIDENTIAL
```

### Options

- `--font-size 54`
  Font size for text watermarks.
- `--angle 45`
  Rotation angle in degrees.
- `--opacity 0.18`
  Transparency from `0.0` to `1.0`.
- `--color 0.2,0.2,0.2`
  Text watermark RGB color as three floats between `0` and `1`.
- `--image-scale 0.45`
  Image watermark width relative to the page width.
- `--compress`
  Runs a second optimization pass with Ghostscript to materially reduce the final file size.
- `--compression-quality medium`
  Quality preset for `--compress`.
  `low` aims for the smallest file, `medium` is a balanced default, `high` keeps more detail, and `max` preserves the most quality while still optimizing.

## Examples

### Default text watermark

```bash
docker compose run --rm watermark-pdf ./pdf/salas2.pdf ./output/salas2-default.pdf
```

### Red draft mark

```bash
docker compose run --rm watermark-pdf ./pdf/salas3.pdf ./output/salas3-draft.pdf --text "DRAFT" --font-size 80 --angle 40 --opacity 0.16 --color 0.85,0.1,0.1
```

### Soft gray review mark

```bash
docker compose run --rm watermark-pdf ./pdf/profs2.pdf ./output/profs2-review.pdf --text "REVIEW COPY" --opacity 0.08 --color 0.3,0.3,0.3
```

### Batch image watermark

```bash
docker compose run --rm watermark-pdf ./pdf ./output --image ./watermarks/wm-pre-launch.png --opacity 0.12 --angle 315 --image-scale 0.50
```

### Batch image watermark with compression

```bash
docker compose run --rm watermark-pdf ./pdf ./output --image ./watermarks/wm-pre-launch.png --opacity 0.12 --angle 315 --image-scale 0.50 --compress --compression-quality low
```

## Repo Layout

- `compose.yaml` Compose service definition and default command wiring
- `Dockerfile`: runtime image with Python dependencies
- `requirements.txt`: pinned Python dependencies
- `watermark_pdf.py`: CLI implementation
- `.env.example`: sample environment values for the compose service
- `pdf/`: sample input PDFs
- `watermarks/`: sample watermark images

## Notes

- If `INPUT` is a file, `OUTPUT` must be a file path, not a directory.
- If `INPUT` is a directory, `OUTPUT` will be created if it does not exist.
- `--color` only affects text watermarks.
- `--image-scale` only affects image watermarks.
- `--compress` requires Ghostscript in the container image, so rebuild with `docker compose build` after pulling these changes.
- The exact size reduction depends on the source PDF structure and the selected `--compression-quality`.
- The watermark image path must exist.
- Non-PDF input files are rejected.

## Troubleshooting

### `docker: command not found`

Install Docker Desktop or another Docker runtime that provides `docker compose`.

### `no such file or directory` for the watermark image

Use one of the repo’s actual image paths:

```bash
./watermarks/wm-review.png
./watermarks/wm-pre-launch.png
```

### Output file was not created

Check:

- the input path exists
- the image path exists if using `--image`
- `OUTPUT` is a file path for single-PDF input
- `docker compose build` completed successfully

## Local Python Alternative

If you prefer not to use Docker, you can still run the script directly:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 watermark_pdf.py ./pdf ./output --text "CONFIDENTIAL"
```
