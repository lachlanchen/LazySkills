# PDF To TeX Toolchain And Script Inventory

Use this reference when documenting, writing, or reviewing code that converts
PDF books into exact TeX/PDF and pocket-size TeX/PDF outputs. Keep project
specific book names, paths, and prompts outside the skill; this file documents
general roles and contracts.

## Tool Categories

| Category | Tools | Role |
| --- | --- | --- |
| PDF inspection | `pdfinfo`, `pdftotext`, `pdfimages`, `pdfseparate`, `qpdf`, `mutool` | Decide whether the PDF is born-digital, scanned, image-heavy, encrypted, or page-image based. |
| Page rendering | `pdftoppm`, `pdftocairo`, ImageMagick `magick`, Poppler | Render evidence images, crop page regions, and create validation screenshots. |
| Text extraction | `pdftotext`, PyMuPDF/`fitz`, `pdfplumber`, `pypdf` | Extract embedded text and layout when available. |
| OCR layout extraction | Marker/Surya, PaddleOCR, Tesseract, Umi-OCR | Convert scanned pages or hard layouts into Markdown/text with page structure. |
| Equation OCR | Mathpix, pix2tex/LaTeX-OCR | Convert formulas to LaTeX. Mathpix is preferred when exactness matters. |
| Table extraction | `pdfplumber`, Camelot, Tabula | Extract born-digital tables into CSV/Markdown/LaTeX. |
| Figure extraction | `pdfimages`, PyMuPDF clips, `pdftocairo` crops | Preserve diagrams, plots, notation, and dense visual regions. |
| Music OMR | Audiveris, MuseScore, LilyPond `musicxml2ly`, `lilypond-book` | Convert staff notation to MusicXML/LilyPond when verification is possible. |
| TeX conversion | Pandoc, custom sanitizers, `latexmk`, `xelatex` | Convert Markdown/body fragments into compilable TeX/PDF. |
| PDF cleanup/compression | Ghostscript, `qpdf`, `ocrmypdf` | Compress or linearize PDFs after validation; do not use these to hide layout errors. |
| Visual comparison | `pdftoppm`, ImageMagick `compare`, perceptual hashes | Compare source/rendered pages during QA. |

## Recommended Script Responsibilities

Prefer small scripts with clear evidence output over monolithic one-off
pipelines. A robust project normally has these responsibilities:

| Script responsibility | Required behavior |
| --- | --- |
| `probe_pdf` | Run `pdfinfo`, `pdftotext`, and `pdfimages`; write JSON with page count, text length, image profile, and route recommendation. |
| `extract_assets` | Extract page images and embedded images into stable folders; never overwrite original source PDFs. |
| `ocr_pages` | Run OCR or layout extraction; cache raw output; record tool version, command, page range, and logs. |
| `normalize_body` | Clean OCR text, join broken paragraphs, normalize Unicode/control chars, rewrite image paths, and preserve page evidence comments. |
| `convert_to_tex` | Convert Markdown or OCR output to a TeX body; keep body separate from wrapper/template. |
| `sanitize_tex` | Fix unsupported macros, image sizing, unsafe table constructs, music/math OCR tokens, and known OCR confusions. |
| `wrap_exact` | Build an exact/review TeX document from the reviewed body. |
| `wrap_pocket` | Build a pocket-size TeX document from the same body with only layout changes. |
| `compile_pdf` | Run XeLaTeX/latexmk in repeatable passes and save logs per pass. |
| `validate_pdf` | Count pages, text chars, missing images, overfulls, severe TeX errors, and sample-page render checks. |
| `write_summary` | Emit `summary.json` with all evidence needed to accept or reject completion. |

## Two-Stage Exact And Editorial Architecture

Keep local reconstruction and model-assisted editorial work as separate
stages. A good exact conversion must not depend on a model, and a later
editorial pass must not rerun OCR or rewrite already accepted technical
objects.

### Stage 1: Local Exact And Pocket Conversion

1. Hash and probe the immutable source.
2. Select EPUB/Pandoc, born-digital PDF extraction, or page-aware OCR according
   to evidence rather than filename.
3. Process long PDFs in resumable page shards and retain raw extraction logs.
4. Normalize transport, Unicode, table, image-path, and TeX defects
   deterministically.
5. Keep exceptional source-backed fixes in count-checked JSON ledgers. Never
   patch the raw OCR cache in place.
6. Build an exact edition first, then derive the pocket edition from the same
   reviewed body.
7. Accept completion only after structure, object inventory, source coverage,
   PDF integrity, TOC, glyph, overflow, and visual checks pass.

Layout-only changes should rebuild from cached extraction. They must not repeat
OCR.

### Stage 2: Optional Evidence-Gated Editorial Polish

Use a model only for unresolved prose correction or translation:

- split content into stable semantic segments;
- replace equations, figures, tables, labels, citations, numbers, and fragile
  TeX commands with protected tokens;
- cache accepted output by source hash and segment id;
- compare protected-token, command, math, number, and object signatures with
  deterministic validators;
- retry only the failing segment, never an otherwise-correct chunk or book;
- repair malformed source evidence before asking the model to translate it;
- assemble and compile only after current-manifest coverage is complete.

Do not let an orchestration layer recursively create retry jobs. One durable
queue owns retry passes; stalled jobs retain evidence and return a concrete
blocked reason.

### Evidence Layout

Prefer this durable structure:

```text
output/<book>/
  source/                 # immutable flattened source snapshot
  tasks/manifest.json     # stable chunks and segment ids
  work/marker-shards/     # local extraction cache when applicable
  work/segment-cache/     # accepted editorial segments
  work/failed/            # concrete unresolved evidence
  exact/tex/book.tex
  exact/book.pdf
  pocket-large-font/tex/book.tex
  pocket-large-font/book.pdf
  review/status.json
```

The status file is authoritative only when its timestamp and live process state
agree. After a reboot or interrupted tmux session, inspect processes and
manifest coverage instead of trusting a stale `running` field.

## Minimal Command Patterns

### Inspect source quality

```bash
pdfinfo input.pdf
pdftotext input.pdf - | wc -m
pdfimages -list input.pdf | sed -n '1,80p'
```

Interpretation:

- high text count plus normal font layout: use text extraction first;
- nearly zero text count plus one large image per page: use OCR;
- many small images/figures plus good text: extract text and preserve figures;
- formulas/tables/music: classify those regions before deciding conversion.

### Render page evidence

```bash
pdftoppm -f 20 -l 20 -png -r 180 input.pdf evidence/page20
pdftocairo -png -r 240 -f 20 -l 20 input.pdf evidence/page20-hires
```

Use rendered source pages to check OCR, equation reconstruction, figure
placement, and pocket legibility.

### Extract figures

```bash
mkdir -p work/images
pdfimages -all input.pdf work/images/page-image
```

For diagrams, labels, music notation, and dense tables, prefer region crops
when full semantic conversion is not verified.

### Run Marker/Surya

```bash
marker_single input.pdf \
  --output_dir work/marker \
  --output_format markdown \
  --highres_image_dpi 240 \
  --disable_tqdm
```

Keep the raw Marker output. Build cleaned TeX from a separate normalized file.

### Convert Markdown to TeX body

```bash
pandoc \
  --from markdown+tex_math_dollars+raw_tex \
  --to latex \
  work/source.md \
  -o work/body.tex
```

The wrapper document should live separately from `body.tex` so exact and pocket
editions can reuse the same reviewed content.

### Compile and validate

```bash
xelatex -interaction=nonstopmode -halt-on-error -output-directory build/exact source.tex
pdfinfo build/exact/book.pdf
pdftotext build/exact/book.pdf - | wc -m
rg -n 'Undefined control sequence|Missing \\$|File `.* not found|Unable to load picture|Overfull' build/exact/*.log
```

Compile exact first, then pocket. Fix content in the shared body whenever
possible; avoid one-off pocket-only content patches.

## Python Helper Patterns

Use `pathlib.Path`, UTF-8 IO, and JSON evidence output. Keep original sources
read-only.

### Probe function shape

```python
def probe_pdf(pdf: Path) -> dict:
    info = run(["pdfinfo", str(pdf)])
    text = run(["pdftotext", str(pdf), "-"])
    images = run(["pdfimages", "-list", str(pdf)])
    return {
        "pages": parse_pages(info.stdout),
        "text_chars": len(text.stdout),
        "image_lines": len(images.stdout.splitlines()),
        "route": choose_route(text.stdout, images.stdout),
    }
```

### Summary schema

```json
{
  "source_pdf": "sources/book/input.pdf",
  "route": "mathpix|marker|text-extract|hybrid",
  "exact_pdf": "build/book/exact/book.pdf",
  "pocket_pdf": "build/book/pocket/book.pdf",
  "pages": 0,
  "text_chars": 0,
  "image_count": 0,
  "missing_image_count": 0,
  "overfull_hbox_count": 0,
  "severe_tex_error_count": 0,
  "suspect_ocr": []
}
```

## Tool-Specific Notes

### Mathpix

- Treat downloaded archives as immutable source caches.
- Record the Mathpix job id or archive path in the project summary.
- Build new TeX/PDF outputs in separate folders.
- Do not manually edit the Mathpix source archive; patch a copied body or an
  overlay fixes file.

### Marker/Surya

- Good for page layout, prose OCR, and mixed image/text documents.
- It may preserve diagrams as images, which is often the correct first exact
  edition.
- It can misread technical/music symbols; maintain auditable fixes.

### pix2tex

- Use on cropped equation regions, not whole pages.
- Always compare rendered formula output to the source crop.
- Preserve a formula as an image when confidence is low.

### Tables

- Use `pdfplumber`/Camelot/Tabula only when table structure is reliable.
- Validate column counts and headers.
- Preserve difficult scanned tables as images with clean captions.

### Music Notation

- Use Audiveris for staff notation: image crop -> MusicXML/MXL.
- Validate MusicXML with MuseScore or Verovio before converting to LilyPond.
- Use `musicxml2ly` and `lilypond-book` only after OMR has passed visual QA.
- For guitar diagrams/fretboards/chord boxes, preserve images first.

## Failure Handling

If compilation fails:

1. read the first fatal TeX error in the log;
2. patch sanitizer rules or a local fixes file, not the original OCR cache;
3. rerun from the cached OCR/body when possible;
4. update `summary.json` and repair notes.

If pocket pages have many overfull formulas:

1. confirm exact edition is correct first;
2. add local display-math wrapping or scaling;
3. split long equations with `aligned`, `split`, or `multline`;
4. use preserved equation figures only for hard cases;
5. rerun sample-page visual checks.

## Completion Gate

A script should not report success from process exit alone. It should require:

- exact TeX exists and exact PDF exists;
- pocket TeX exists and pocket PDF exists;
- source and output page counts are plausible;
- output text extraction is non-trivial;
- missing image count is zero;
- severe TeX error count is zero;
- overfulls are reviewed;
- representative source/rendered pages are checked.
