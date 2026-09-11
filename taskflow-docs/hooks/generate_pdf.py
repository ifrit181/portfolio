"""mkdocs hook: generate a PDF for every page in the navigation.

On ``on_post_build`` the hook:
  1. renders each page's DOCX in memory (avto_doc/generate_single.py);
  2. converts it to PDF with headless LibreOffice (twice: the first pass
     supplies the page numbers for the table of contents, because LibreOffice
     renders the cached TOC field result and does not recompute it);
  3. saves the PDF to ``site/assets/pdf/<page>.pdf``;
  4. deletes the temporary DOCX — only the PDF is shipped with the site.

Pages that are not part of ``nav`` (e.g. markdown fragments in ``snippets/``)
are skipped.
"""

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

LOGGER = logging.getLogger("mkdocs")


def _import_generator():
    """Import avto_doc.generate_single from within the taskflow-docs tree."""
    hook_dir = Path(__file__).resolve().parent          # .../taskflow-docs/hooks
    avto_doc = hook_dir.parent / "avto_doc"
    sys.path.insert(0, str(avto_doc))
    import generate_single
    return generate_single


def _iter_nav_files(nav):
    """Yield markdown source paths (relative to docs_dir) from a nav value,
    tolerating both the config form ({title: path} dicts) and the built form
    ((title, item) tuples)."""
    if nav is None:
        return
    if not isinstance(nav, (list, tuple)):
        nav = [nav]
    for entry in nav:
        if isinstance(entry, dict):
            for value in entry.values():
                yield from _iter_nav_files(value)
        elif isinstance(entry, (list, tuple)) and len(entry) == 2 and isinstance(entry[0], str):
            yield from _iter_nav_files(entry[1])
        elif isinstance(entry, (list, tuple)):
            yield from _iter_nav_files(list(entry))
        elif isinstance(entry, str):
            yield entry
        elif hasattr(entry, "src_path"):
            yield entry.src_path


def _to_pdf(docx_path: Path, out_dir: Path, profile_dir: Path) -> Path:
    """Convert a DOCX to PDF via headless LibreOffice, return the PDF path."""
    cmd = [
        "soffice",
        "--headless",
        "-env:UserInstallation=file://" + profile_dir.as_posix(),
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx_path),
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"LibreOffice failed for {docx_path.name}:\n{res.stdout}\n{res.stderr}"
        )
    pdf = out_dir / f"{docx_path.stem}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not produced for {docx_path.name}")
    return pdf


_MASK_INVERT = bytes(0xFF - b for b in range(256))


def _extract_heading_pages(pdf_path: Path, entries) -> dict:
    """Map heading text -> 1-based PDF page number.

    A heading's page is found by exact line match: the body renders each
    heading as its own line (e.g. "1.1 Загрузка сотрудников") while the TOC
    entry line ends with dot leaders and a page number, so it never matches
    exactly. For the rare case where a heading's exact text line does not
    appear standalone, the page of the previous heading is reused.
    """
    reader = PdfReader(str(pdf_path))
    page_lines = []
    page_texts = []
    for i, pg in enumerate(reader.pages):
        text = (pg.extract_text() or "").replace("\u00a0", " ")
        lines = [ln for ln in text.split("\n") if ln.strip()]
        page_lines.append(([" ".join(ln.split()) for ln in lines], i + 1))
        page_texts.append(" ".join(lines))

    mapping = {}
    last_page = str(max(1, len(reader.pages)))
    for _lvl, text in entries:
        target = " ".join(text.replace("\u00a0", " ").split())
        found = None
        for lines, num in page_lines:
            if target in lines:
                found = num
                break
        if found is None and target:
            for i, t in enumerate(page_texts):
                if target in t:
                    found = i + 1
                    break
        if found is not None:
            last_page = str(found)
        mapping[text] = last_page
    return mapping


def _fix_soft_masks(pdf_path: Path) -> Path:
    """Make image transparency render correctly in every PDF viewer.

    LibreOffice stores translucent PNGs on the cover as JPEG (DCTDecode) plus a
    grayscale soft mask carrying /Decode [1 0]. Several viewers mishandle
    /Decode on soft masks and paint the transparent areas black. Rewrite such
    masks without /Decode, inverting the samples so the rendered result is
    byte-for-byte identical in correct renderers and the ones that would have
    failed are fixed too.
    """
    writer = PdfWriter(clone_from=str(pdf_path))
    changed = 0
    for page in writer.pages:
        res = page.get("/Resources")
        xobjs = (res.get("/XObject") if res else {}) or {}
        for ref in xobjs.values():
            xobj = ref.get_object()
            if xobj.get("/Subtype") != "/Image":
                continue
            sm_ref = xobj.get("/SMask")
            if sm_ref is None:
                continue
            sm = sm_ref.get_object()
            if "/Decode" not in sm:
                continue
            decode = list(sm.get("/Decode"))
            if tuple(round(float(v), 3) for v in decode) != (1.0, 0.0):
                continue
            width, height = int(sm.get("/Width")), int(sm.get("/Height"))
            data = sm.get_data()
            if len(data) != width * height:
                LOGGER.warning(
                    "generate_pdf: unexpected soft-mask size in %s, skipped",
                    pdf_path.name,
                )
                continue
            sm.set_data(data.translate(_MASK_INVERT))
            sm.pop("/Decode", None)
            changed += 1
    if not changed:
        return pdf_path
    LOGGER.info("generate_pdf: normalised %d soft masks in %s", changed, pdf_path.name)
    fixed = pdf_path.with_name(pdf_path.stem + ".fixed.pdf")
    with fixed.open("wb") as fh:
        writer.write(fh)
    return fixed


def on_post_build(config):
    # Allow skipping PDF generation during local dev (e.g. mkdocs serve),
    # where re-converting every page on each rebuild is too slow.
    if os.environ.get("DOCX2PDF", "1").strip().lower() in {"0", "off", "false", "no"}:
        LOGGER.info("generate_pdf: disabled via DOCX2PDF=off")
        return

    gen = _import_generator()

    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])
    src_files = sorted(set(_iter_nav_files(config.get("nav"))))

    with tempfile.TemporaryDirectory(prefix="docx2pdf-") as tmp:
        tmp = Path(tmp)
        work = tmp / "work"
        profile = tmp / "profile"
        pdfs_dir = tmp / "pdfs"
        work.mkdir()
        pdfs_dir.mkdir()

        for src in src_files:
            src_path = Path(src)
            if src_path.suffix.lower() != ".md":
                continue
            md_path = (docs_dir / src_path).resolve()
            if not md_path.exists():
                LOGGER.warning("generate_pdf: source not found, skipped: %s", src)
                continue

            # Pass A: build the DOCX with the real TOC entries (placeholder
            # page numbers) so the layout is final, convert, and read each
            # heading's real page number from the resulting PDF.
            try:
                entries, docx_pass_a = gen.render_docx_with_toc(md_path)
                toc_map = {}
                if entries:
                    pass_a = work / f"{src_path.stem}_pass-a.docx"
                    pass_a.write_bytes(docx_pass_a)
                    try:
                        pdf_a = _to_pdf(pass_a, pdfs_dir, profile)
                        toc_map = _extract_heading_pages(pdf_a, entries)
                    finally:
                        try:
                            pass_a.unlink()
                        except OSError:
                            pass
                # Pass B: same document, now with the correct cached page numbers.
                _, docx_bytes = gen.render_docx_with_toc(md_path, toc_pages=toc_map)
            except Exception as exc:
                LOGGER.warning("generate_pdf: DOCX failed for %s: %s", src, exc)
                continue

            docx_path = work / f"{src_path.stem}.docx"
            docx_path.write_bytes(docx_bytes)

            try:
                pdf = _to_pdf(docx_path, pdfs_dir, profile)
                pdf = _fix_soft_masks(pdf)
            except Exception as exc:
                LOGGER.warning("generate_pdf: PDF failed for %s: %s", src, exc)
                continue
            finally:
                # DOCX is intermediate only — never ship it
                try:
                    docx_path.unlink()
                except OSError:
                    pass

            out = site_dir / "assets" / "pdf" / src_path.with_suffix(".pdf")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(pdf.read_bytes())
            LOGGER.info("generate_pdf: %s", out.relative_to(site_dir))