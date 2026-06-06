---
name: ocr-book-polisher
description: Use when converting scanned PDFs, image-heavy books, OCR output, or rough Markdown into a corrected, publishable text/TeX/PDF book while preserving figures, captions, source structure, and evidence-based validation.
triggers:
  - OCR scanned book
  - scanned PDF to TeX
  - polished OCR markdown
  - correct OCR errors
  - preserve figures and captions
  - booklike TeX
  - fix generated TOC
  - searchable PDF to clean book
---

# OCR Book Polisher

Use this skill for scanned or image-heavy books that need more than a hidden text layer: the output should read like a newly typeset book, with corrected text, real headings, figures, captions, and a reliable table of contents.

## Core Rules

- Fix the body, not only the generated TOC. If the TOC is wrong, locate the corresponding content heading and correct or insert it in the source text.
- Preserve images and captions when the original book contains meaningful figures. Remove placeholder prose such as “original page image” unless the user explicitly wants a facsimile.
- Treat OCR as suspect until checked against source evidence. Correct obvious recognition errors, garbled Latin fragments, broken captions, and misread headings.
- Keep old outputs if requested, but put new editions in a clear folder such as `build/<book>-polished-tex/` or `build/<book>-booklike-pocket/`.
- Validate before claiming completion: generated PDF path, page count, TOC, log warnings, and a spot check of representative pages.

## Workflow

1. Inventory sources and current artifacts:

```bash
git status --short
find sources books build -maxdepth 3 -iname '*BOOK*' -o -iname '*.pdf' -o -iname '*.md'
```

2. Extract or OCR into page-aware Markdown. Preserve page markers and page kind metadata, for example:

```markdown
## Page 18
<!-- kind=text confidence=medium -->
### Chapter Heading
正文……
```

3. Build a real structural map from the source book:

- Use the original contents pages, title pages, and body starts.
- Map printed page numbers to physical/OCR page numbers.
- Insert missing body headings where chapters actually begin.
- Mark noisy OCR headings as local headings, not TOC entries.

4. Polish text page by page:

- Join broken paragraphs and restore punctuation.
- Correct OCR confusions by comparing neighboring context and source images.
- Rewrite captions into clean captions; do not drop captions silently.
- For figure pages, prefer full-page figures in pocket editions unless the layout requires otherwise.

5. Render TeX/PDF with a strict heading policy for fragile books. Only allow verified headings into the TOC. Incidental headings should render as visible local headings without entering the TOC.

6. Validate:

```bash
python -m py_compile scripts/**/*.py
xelatex -interaction=nonstopmode -halt-on-error ...
pdfinfo build/.../book.pdf
rg -n 'Overfull|Underfull|Warning|Error' build/.../*.log
sed -n '1,200p' build/.../*.toc
```

## Completion Checklist

- Correct title and metadata match the source.
- TOC entries correspond to real body headings.
- Figures and captions are present and readable.
- No placeholder page labels remain in the booklike edition.
- No severe overfull lines or compile errors remain.
- Output PDF is synced to the requested destination when applicable.
- Tracked source/script changes are committed; original large source files remain uncommitted unless explicitly requested.
