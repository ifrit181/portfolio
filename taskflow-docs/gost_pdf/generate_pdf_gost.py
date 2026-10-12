"""mkdocs hook / CLI: сборка PDF с оформлением по ГОСТ.

Отдельная копия `hooks/generate_pdf.py` с ГОСТ-постобработкой
(`gost_pdf/titlepage.py`, `gost_pdf/gost_styles.py`). Вывод —
`site/assets/pdf-gost/`; в `mkdocs.yml` хук не подключается.

Запуск из CLI::

    python gost_pdf/generate_pdf_gost.py [--docs-dir docs] [--site-dir site]
        [--doc-type rukovodstvo-polzovatelya] [--only index.md,faq.md]
"""

from __future__ import annotations

import argparse
import datetime
import io
import logging
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from pypdf import PdfReader, PdfWriter

LOGGER = logging.getLogger("mkdocs")

HOOK_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = HOOK_DIR.parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

import doc_types
import gost_check
import gost_styles
import titlepage

_FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?\r?\n)?---[ \t]*(?:\r?\n|\Z)", re.S)
RENAME = gost_styles.RENAME


def _import_generator():
    avto_doc = PROJECT_ROOT / "avto_doc"
    if str(avto_doc) not in sys.path:
        sys.path.insert(0, str(avto_doc))
    import generate_single

    import gost_base

    # ГОСТ-генератор не зависит от primer.docx: базовый документ
    # (стили, скелеты ЛИ/содержания) строится программно, титул —
    # titlepage.py, оформление — gost_styles.py.
    generate_single._fresh_doc = gost_base.fresh_gost_doc
    generate_single._template_warning_xml = gost_base.template_warning_xml
    generate_single._title_page = lambda *args, **kwargs: None
    generate_single._fit_title_page = lambda *args, **kwargs: None
    return generate_single


def _split_front_matter(text: str) -> tuple[dict, str]:
    text = text.lstrip("\ufeff")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except Exception:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[m.end():]


def _flag(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on", "да"}


def _s(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _collect_ctx(meta: dict, doc_type_override: str | None, sheets=None) -> dict:
    doc_type = doc_types.resolve(doc_type_override or meta.get("gost_doc_type"))
    annotation = meta.get("gost_annotation")
    return {
        "doc_type": doc_type,
        "product_name": _s(meta.get("gost_product_name")) or None,
        "oboznachenie": _s(meta.get("gost_oboznachenie")),
        "litera": _s(meta.get("gost_litera")),
        "otmetka_ucheta": _s(meta.get("gost_otmetka_ucheta")),
        "stroka_izmenenij": _s(meta.get("gost_stroka_izmenenij")),
        "lu_oboznachenie": _s(meta.get("gost_lu_oboznachenie")),
        "ministerstvo": _s(meta.get("gost_ministerstvo")),
        "author": _s(meta.get("gost_author")),
        "left30": _flag(meta.get("gost_left_margin_30")),
        "annotation": "" if annotation is None else str(annotation),
        "sheets": sheets,
    }


def render_docx_gost(gen, md_path: Path, ctx: dict, toc_pages: dict | None = None):
    """MD → DOCX с ГОСТ-титулом и рестайлом; возвращает (entries, bytes)."""
    text = Path(md_path).read_text(encoding="utf-8-sig")
    _, body = _split_front_matter(text)
    tmp = Path(md_path).parent / (".gost-tmp-" + Path(md_path).name)
    tmp.write_text(body, encoding="utf-8")
    try:
        product_name = ctx["product_name"]
        if product_name is None:
            headings = gen._extract_headings(tmp)
            product_name = next(
                (t for lvl, t in headings if lvl == 1), tmp.stem
            )
        ctx["product_name_used"] = product_name
        doc, _, _, entries = gen._prepare_docx(tmp, product_name, toc_pages)

        titlepage.apply(
            doc,
            product_name=product_name,
            doc_type_title=ctx["doc_type"].title,
            oboznachenie=ctx["oboznachenie"],
            litera=ctx["litera"],
            otmetka_ucheta=ctx["otmetka_ucheta"],
            stroka_izmenenij=ctx["stroka_izmenenij"],
            lu_oboznachenie=ctx["lu_oboznachenie"],
            ministerstvo=ctx["ministerstvo"],
            sheets=ctx["sheets"],
            year=datetime.date.today().year,
            left30=ctx["left30"],
        )
        gost_styles.apply(
            doc,
            entries=entries,
            doc_type=ctx["doc_type"],
            oboznachenie=ctx["oboznachenie"],
            stroka_izmenenij=ctx["stroka_izmenenij"],
            annotation=ctx["annotation"],
            left30=ctx["left30"],
        )
        doc.core_properties.author = (
            ctx.get("author") or gen._latest_doc_author()
        )

        buf = io.BytesIO()
        doc.save(buf)
        return entries, buf.getvalue()
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass


def _iter_nav_files(nav):
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


def _walk_docs(docs_dir: Path):
    for p in sorted(docs_dir.rglob("*.md")):
        rel = p.relative_to(docs_dir)
        if p.name.startswith("."):
            continue
        if "snippets" in rel.parts:
            continue
        yield str(rel).replace("\\", "/")


def _to_pdf(docx_path: Path, out_dir: Path, profile_dir: Path) -> Path:
    cmd = [
        "soffice",
        "--headless",
        "-env:UserInstallation=" + profile_dir.as_uri(),
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(docx_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        raise RuntimeError(
            f"LibreOffice failed for {docx_path.name}:\n{res.stdout}\n{res.stderr}"
        )
    pdf = out_dir / f"{docx_path.stem}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(f"PDF not produced for {docx_path.name}")
    return pdf


def _norm_line(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split()).casefold()


def _extract_heading_pages(pdf_path: Path, entries) -> dict:
    reader = PdfReader(str(pdf_path))
    page_lines = []
    page_texts = []
    for i, pg in enumerate(reader.pages):
        text = (pg.extract_text() or "").replace("\u00a0", " ")
        lines = [_norm_line(ln) for ln in text.split("\n") if ln.strip()]
        page_lines.append((lines, i + 1))
        page_texts.append(" ".join(lines))

    toc_pages = {
        i for i, (lines, _) in enumerate(page_lines) if "содержание" in lines
    }

    mapping = {}
    last_page = str(max(1, len(reader.pages)))
    for _lvl, text in entries:
        target = _norm_line(RENAME.get(text, text))
        found = None
        if target:
            for lines, num in page_lines:
                if target in lines:
                    found = num
                    break
            if found is None:
                for i, t in enumerate(page_texts):
                    if i in toc_pages:
                        continue
                    if target in t:
                        found = i + 1
                        break
        if found is not None:
            last_page = str(found)
        mapping[text] = last_page
    return mapping


_MASK_INVERT = bytes(0xFF - b for b in range(256))


def _fix_soft_masks(pdf_path: Path) -> Path:
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
                    "generate_pdf_gost: unexpected soft-mask size in %s, skipped",
                    pdf_path.name,
                )
                continue
            sm.set_data(data.translate(_MASK_INVERT))
            sm.pop("/Decode", None)
            changed += 1
    if not changed:
        return pdf_path
    fixed = pdf_path.with_name(pdf_path.stem + ".fixed.pdf")
    with fixed.open("wb") as fh:
        writer.write(fh)
    return fixed


def _warn_sections(rel: str, ctx: dict, entries):
    doc_type = ctx["doc_type"]
    headings = [t for lvl, t in (entries or []) if lvl <= 2]
    missing = doc_types.missing_sections(doc_type, headings)
    if missing:
        LOGGER.warning(
            "generate_pdf_gost: %s: нет обязательных разделов (%s, %s): %s",
            rel, doc_type.title, doc_type.content_standard, ", ".join(missing),
        )
    if doc_type.info_part and not ctx["annotation"].strip():
        LOGGER.warning(
            "generate_pdf_gost: %s: не задана gost_annotation "
            "(информационная часть обязательна для «%s»)",
            rel, doc_type.title,
        )


def on_post_build(config, *, doc_type=None, only=None, report=None):
    if os.environ.get("DOCX2PDF", "1").strip().lower() in {"0", "off", "false", "no"}:
        LOGGER.info("generate_pdf_gost: disabled via DOCX2PDF=off")
        return

    gen = _import_generator()
    docs_dir = Path(config["docs_dir"])
    site_dir = Path(config["site_dir"])
    nav = config.get("nav")
    if nav is not None:
        src_files = sorted({_norm_rel(s) for s in _iter_nav_files(nav)})
    else:
        src_files = sorted(_walk_docs(docs_dir))

    only_set = None
    if only:
        if isinstance(only, str):
            only_set = {_norm_rel(s) for s in only.split(",") if s.strip()}
        else:
            only_set = {_norm_rel(s) for s in only}

    reports: list[gost_check.DocReport] = []
    started = datetime.datetime.now()

    with tempfile.TemporaryDirectory(prefix="gost-pdf-") as tmp:
        tmp = Path(tmp)
        work = tmp / "work"
        profile = tmp / "profile"
        pdfs_dir = tmp / "pdfs"
        work.mkdir()
        pdfs_dir.mkdir()

        for rel in src_files:
            if only_set is not None and rel not in only_set:
                continue
            rep = gost_check.DocReport(rel=rel)
            reports.append(rep)
            md_path = (docs_dir / rel).resolve()
            if not md_path.exists():
                rep.error = "исходник не найден"
                LOGGER.warning("generate_pdf_gost: source not found, skipped: %s", rel)
                continue
            try:
                meta, _ = _split_front_matter(md_path.read_text(encoding="utf-8-sig"))
            except OSError:
                meta = {}
            ctx = _collect_ctx(meta, doc_type)
            rep.doc_type = ctx["doc_type"].title
            rep.standard = ctx["doc_type"].content_standard
            flat = re.sub(r"[^A-Za-z0-9._-]+", "_", rel)

            pdf_out = None
            docx_a = work / f"{flat}.a.docx"
            docx_b = work / f"{flat}.b.docx"
            try:
                entries, docx_bytes_a = render_docx_gost(gen, md_path, ctx)
                _warn_sections(rel, ctx, entries)
                docx_a.write_bytes(docx_bytes_a)
                pdf_a = _to_pdf(docx_a, pdfs_dir, profile)
                toc_map = _extract_heading_pages(pdf_a, entries) if entries else {}
                sheets = len(PdfReader(str(pdf_a)).pages)
                ctx["sheets"] = sheets

                _, docx_bytes_b = render_docx_gost(gen, md_path, ctx, toc_map)
                docx_b.write_bytes(docx_bytes_b)
                pdf = _to_pdf(docx_b, pdfs_dir, profile)
                pdf_out = _fix_soft_masks(pdf)
            except Exception as exc:
                rep.error = f"{type(exc).__name__}: {exc}"
                LOGGER.warning("generate_pdf_gost: failed for %s: %s", rel, exc)
                continue
            finally:
                for p in (docx_a, docx_b):
                    try:
                        p.unlink()
                    except OSError:
                        pass

            out = site_dir / "assets" / "pdf-gost" / Path(rel).with_suffix(".pdf")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(pdf_out.read_bytes())
            LOGGER.info("generate_pdf_gost: %s", out)
            rep.out = str(Path("assets") / "pdf-gost"
                          / Path(rel).with_suffix(".pdf")).replace("\\", "/")
            try:
                gost_check.check_pdf(pdf_out, ctx, entries, rep)
            except Exception as exc:
                rep.add(gost_check.FAIL, "Проверка",
                        f"не удалось проверить PDF: {type(exc).__name__}: {exc}")

    _write_report(reports, site_dir, started, only=only, report_path=report)


def _write_report(reports, site_dir: Path, started, *, only, report_path) -> None:
    if report_path is None:
        out = site_dir / "assets" / "pdf-gost" / "check-report.md"
    elif str(report_path).strip().lower() in {"off", "0", "false", "no"}:
        return
    else:
        out = Path(report_path)
    if not out.is_absolute():
        out = site_dir / out
    out.parent.mkdir(parents=True, exist_ok=True)
    if started is None:
        started = datetime.datetime.now()
    only_str = None
    if only:
        only_str = only if isinstance(only, str) else ",".join(only)
    text = gost_check.build_report(
        reports,
        timestamp=started.strftime("%Y-%m-%d %H:%M:%S"),
        only=only_str,
    )
    out.write_text(text, encoding="utf-8")
    n_fail = sum(1 for r in reports if r.level == gost_check.FAIL)
    n_warn = sum(1 for r in reports if r.level == gost_check.WARN)
    LOGGER.info(
        "generate_pdf_gost: check report: %s (документов: %d, OK: %d, "
        "предупреждений: %d, ошибок: %d)",
        out, len(reports), len(reports) - n_warn - n_fail, n_warn, n_fail,
    )


def _norm_rel(value) -> str:
    return str(value).replace("\\", "/").strip().lstrip("/")


def _main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(
        description="Сборка PDF по ГОСТ в site/assets/pdf-gost/"
    )
    parser.add_argument("--docs-dir", default=str(PROJECT_ROOT / "docs"))
    parser.add_argument("--site-dir", default=str(PROJECT_ROOT / "site"))
    parser.add_argument("--doc-type", default=None,
                        help="переопределить вид документа для всех файлов")
    parser.add_argument("--only", default=None,
                        help="файлы через запятую (пути относительно docs-dir)")
    parser.add_argument("--report", default=None,
                        help="файл отчёта проверки (по умолчанию "
                             "site/assets/pdf-gost/check-report.md; "
                             "off — не писать)")
    args = parser.parse_args(argv)
    on_post_build(
        {"docs_dir": args.docs_dir, "site_dir": args.site_dir},
        doc_type=args.doc_type,
        only=args.only,
        report=args.report,
    )


if __name__ == "__main__":
    _main()
