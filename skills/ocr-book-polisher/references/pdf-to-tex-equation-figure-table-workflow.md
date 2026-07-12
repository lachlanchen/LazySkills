# High-Quality PDF To TeX Workflow

Use this reference when a book contains equations, figures, tables, diagrams,
music notation, chord charts, technical exercises, or dense scanned pages.

For concrete executable tools, script responsibilities, and validation command
patterns, see `pdf-to-tex-toolchain-and-scripts.md`.

## Current Capability

We have a strong hybrid PDF-to-TeX pipeline, but there is no single local tool
that reliably equals Mathpix on every page type.

Recommended routes:

| Page type | Best route | Local fallback |
| --- | --- | --- |
| Born-digital prose PDF | `pdftotext`, `mutool`, `pymupdf`, Pandoc cleanup | Marker/Surya if layout is hard |
| Scanned prose book | Marker/Surya OCR to Markdown, then TeX cleanup | Tesseract/PaddleOCR/Umi-OCR plus manual polish |
| Equations and math textbooks | Mathpix PDF-to-LaTeX as gold standard | Marker/Surya + pix2tex for formula regions |
| Figures and diagrams | Extract or crop source figures, reference them from TeX | Preserve page region as image if semantic conversion is risky |
| Tables | Native table extraction when reliable; otherwise clean `tabularx`/`longtable` by hand | `pdfplumber`, Camelot/Tabula for born-digital PDFs |
| Music staff notation | Audiveris OMR to MusicXML, then LilyPond | Preserve notation as figure if OMR is uncertain |
| Guitar diagrams/chord boxes/fretboards | Preserve as high-resolution figures first | Rebuild manually only when required |

Mathpix output is expensive and should be treated as a read-only source cache.
Never overwrite downloaded Mathpix archives. Build new exact and pocket outputs
in separate folders.

## Artifact Contract

For each converted technical book, create both layers:

```text
build/<book>-<route>-exact-book/
  exact/source.tex
  exact/<book>-<route>-exact.pdf
  exact/summary.json
  pocket/source.tex
  pocket/<book>-<route>-pocket.pdf
  pocket/summary.json
  work/body.tex
  work/source.md        # when the route starts from Markdown/OCR
```

The exact layer is for reverse-engineering and proofing. It should be close to
the source page order and preserve all content. The pocket layer changes only
layout, font size, margins, and figure scaling. Do not fix content only in the
pocket layer.

Each `summary.json` should record:

- PDF path and page count;
- extracted text character count;
- figure/image count;
- missing image count;
- overfull/underfull counts;
- suspicious OCR lines or repair notes.

## Route Selection

1. Inspect the PDF before OCR:

```bash
pdfinfo input.pdf
pdftotext input.pdf - | wc -m
pdfimages -list input.pdf | sed -n '1,40p'
```

If `pdftotext` yields real prose, prefer a text-extraction route and preserve
images separately. If text extraction is nearly empty and every page is one
large image, use OCR.

2. Classify page regions:

- prose;
- equations;
- tables;
- figures/diagrams;
- music notation;
- captions;
- exercises/problems.

3. Choose the lowest-risk representation for each region:

- real TeX text for prose;
- real LaTeX math for equations when confidence is high;
- `tabularx`/`longtable` for reliable tables;
- high-resolution figure assets for diagrams, notation, and ambiguous regions.

## Equations

Preferred: Mathpix whole-PDF TeX when quality matters and quota is available.

Local route:

- run Marker/Surya for page structure and Markdown;
- run pix2tex or another formula OCR on cropped equation regions;
- compare formula OCR against the source image;
- keep hard multi-line derivations as source-cropped figures until verified.

Validation:

```bash
xelatex -interaction=nonstopmode -halt-on-error source.tex
rg -n 'Missing \\$|Undefined control sequence|Overfull|File `.* not found' *.log
pdftotext output.pdf - | wc -m
```

For pocket layouts, formula overfulls are expected until explicitly repaired.
Repair with display breaks, smaller local math font, `aligned`, `split`,
`multline`, or preserved equation figures. Do not silently clip formulas.

## Figures And Diagrams

Preserve visual assets before semantic cleanup:

```bash
pdfimages -all input.pdf extracted/image
pdftocairo -png -r 240 -f 12 -l 12 input.pdf page
```

Use full-page or region crops when a diagram contains dense labels, geometry,
music, fretboards, or pedagogical arrows. Captions should be clean text in TeX
when possible, not OCR noise embedded in the image.

Validation:

- every referenced figure exists;
- figure count is plausible against the source;
- no `File not found` or `Unable to load picture` in the LaTeX log;
- sample pages show figures legible at pocket size.

## Tables

Born-digital PDFs can often use `pdfplumber`, Camelot, or Tabula. Scanned
tables usually need OCR plus manual structure repair.

Table rules:

- prefer `tabularx`, `longtable`, or `booktabs`;
- keep units and column headers;
- never merge numeric columns into prose;
- if table OCR is unreliable, preserve the table as a figure and add a clean
caption or summary.

## Music Notation

Music notation is OMR, not ordinary OCR.

Best open-source route:

```text
staff image crop -> Audiveris -> MusicXML/MXL -> musicxml2ly -> LilyPond -> LaTeX/PDF
```

Use Audiveris for staff notation only when the source is clear enough to
validate. Use LilyPond or `lilypond-book` to embed the result in TeX.

For guitar technique/theory books, chord boxes, fretboards, staff examples, and
rhythmic figures should first be preserved as high-quality figures. Convert to
editable LilyPond only after the exact book is already complete.

## Cleanup Patterns

Common technical/music OCR confusions:

| Bad OCR | Likely correction |
| --- | --- |
| `rnusic`, `rnodern`, `cornmon` | `music`, `modern`, `common` |
| `G(^beta)`, `B(^beta)` | `G\flat`, `B\flat` |
| `F(^pe)` or similar | `F\sharp` |
| `quitar` in music context | `guitar` |
| `dvads` in interval context | `dyads` |

Apply these as auditable source/body fixes, then recompile. Keep a local fixes
file if the project supports one.

## Completion Standard

Do not call a technical PDF-to-TeX conversion complete until:

- exact TeX and exact PDF compile;
- pocket TeX and pocket PDF compile;
- text is searchable and not only a facsimile layer;
- all figures/tables/equations/notation are present;
- severe LaTeX errors are zero;
- missing image count is zero;
- overfull lines are reviewed, fixed, or explicitly accepted with evidence;
- representative source pages are compared against rendered output.
