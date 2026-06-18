# watermark-pdf

CLI utility for applying a text or image watermark to PDF files, with the default workflow running through Docker Compose.

It supports:

- one input PDF to one output PDF
- one input directory to one output directory
- text or image watermarks

The source PDFs are left untouched. Watermarks are merged into new output files.

## Requirements

- Docker
- Docker Compose v2 (`docker compose`)

## Quick Start

Build the image once:

```bash
docker compose build
```

Run the tool with Compose:

```bash
docker compose run --rm watermark-pdf INPUT OUTPUT [options]
```

Example:

```bash
docker compose run --rm watermark-pdf \
  ./pdf/salas1.pdf \
  ./output/salas1-watermarked.pdf \
  --image ./watermarks/watermark.png \
  --angle 315 \
  --opacity 0.25
```

## Manual

### 1. Build the container

```bash
docker compose build
```

This installs the Python dependencies from `requirements.txt` inside the image. You do not need to install `pypdf` or `reportlab` locally.

### 2. Watermark a single PDF with text

```bash
docker compose run --rm watermark-pdf \
  ./pdf/profs1.pdf \
  ./output/profs1-confidential.pdf \
  --text "CONFIDENTIAL"
```

### 3. Watermark a single PDF with an image

```bash
docker compose run --rm watermark-pdf \
  ./pdf/turmas1.pdf \
  ./output/turmas1-review.pdf \
  --image ./watermarks/watermark.png \
  --angle 315 \
  --opacity 0.25 \
  --image-scale 0.45
```

### 4. Process an entire directory

```bash
docker compose run --rm watermark-pdf \
  ./pdf \
  ./output \
  --text "INTERNAL"
```

When the input is a directory, the script:

- scans for `*.pdf` files recursively
- creates the output directory automatically
- preserves the input directory structure inside the output directory

### 5. Use the helper script

The repo includes [run.sh](run.sh), which loads `.env` from the repository root before running Compose:

```bash
./run.sh
```

Current `.env` values look like this:

```bash
WATERMARK_FILE=./watermarks/watermark.png
WATERMARK_ANGLE=35
WATERMARK_OPACITY=0.25
WATERMARK_SCALE=1
PDF_PATH=./pdf
```

You can edit `.env` to change the default input PDF directory, watermark file, angle, or opacity without changing the script.

## Usage

### Command format

```bash
docker compose run --rm watermark-pdf INPUT OUTPUT [options]
```

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

The `run.sh` wrapper also forwards `WATERMARK_SCALE` to `--image-scale`.

## Examples

### Default text watermark

```bash
docker compose run --rm watermark-pdf \
  ./pdf/salas2.pdf \
  ./output/salas2-default.pdf
```

### Red draft mark

```bash
docker compose run --rm watermark-pdf \
  ./pdf/salas3.pdf \
  ./output/salas3-draft.pdf \
  --text "DRAFT" \
  --font-size 80 \
  --angle 40 \
  --opacity 0.16 \
  --color 0.85,0.1,0.1
```

### Soft gray review mark

```bash
docker compose run --rm watermark-pdf \
  ./pdf/profs2.pdf \
  ./output/profs2-review.pdf \
  --text "REVIEW COPY" \
  --opacity 0.08 \
  --color 0.3,0.3,0.3
```

### Batch image watermark

```bash
docker compose run --rm watermark-pdf \
  ./pdf \
  ./output \
  --image ./watermarks/watermark.png \
  --opacity 0.12 \
  --angle 315 \
  --image-scale 0.50
```

## Repo Layout

- [compose.yaml](compose.yaml): Compose service definition
- [Dockerfile](Dockerfile): runtime image with Python dependencies
- [requirements.txt](requirements.txt): pinned Python dependencies
- [watermark_pdf.py](watermark_pdf.py): CLI implementation
- `pdf/`: sample input PDFs
- `watermarks/`: sample watermark images

## Notes

- If `INPUT` is a file, `OUTPUT` must be a file path, not a directory.
- If `INPUT` is a directory, `OUTPUT` will be created if it does not exist.
- `--color` only affects text watermarks.
- `--image-scale` only affects image watermarks.
- The watermark image path must exist.
- Non-PDF input files are rejected.

## Troubleshooting

### `docker: command not found`

Install Docker Desktop or another Docker runtime that provides `docker compose`.

### `no such file or directory` for the watermark image

Use the repo’s actual image path:

```bash
./watermarks/watermark.png
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
