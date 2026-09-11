#!/usr/bin/env python3
"""Генерация DOCX из одного markdown-файла с оглавлением по его содержанию.

Преобразует один .md-файл в Word-документ (.docx), используя шаблон primer.docx
из директории avto_doc/. Заголовки MD-файла автоматически становятся
структурами разделов документа и попадают в оглавление.

Аргументы:
    md_file          Путь к markdown-файлу (абсолютный или относительный).

Опциональные аргументы:
    --output-dir     Каталог для выходного DOCX.
                     По умолчанию — поддиректория output рядом с MD-файлом.
    --product-name   Название продукта для титульной страницы.
                     По умолчанию — текст первого H1 из MD-файла.

Примеры:
    # Базовое использование (название берётся из первого H1 файла):
    python generate.py "Как настроить рейсы ПДМ на бортовом ПО.md"

    # Указать каталог вывода и название продукта:
    python generate.py my_guide.md --output-dir ./build --product-name "Мой продукт"

    # Относительный путь к MD (от корня проекта taskflow-docs):
    python generate_single.py "docs/getting-started/quick-start.md"

Что генерируется:
    1. Титульная страница (по шаблону primer.docx)
    2. Раздел «Изменения в документе» (таблица версий; предупреждение —
       только если MD содержит ``!!! warning``, таблица берётся из шаблона)
    3. Раздел «Содержание» (автообновляемое Word-поле TOC по заголовкам MD)
    4. Основное содержимое MD-файла с нумерацией разделов
    5. Колонтитуры (название в шапке, копирайт в подвале)

Разделы 2-4, колонтитулы и оформление (цвета, размеры шрифтов, стили
таблиц и подписей) берутся из шаблона primer.docx. Скрипт не содержит
жёстких значений оформления: они читаются из стилей/элементов шаблона.
Хардкод остался только в fallback-ветках для шаблонов, в которых
соответствующего элемента просто нет.
"""

import argparse
import copy
import datetime
from xml.sax.saxutils import escape as _xml_escape
import io
import os
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from lxml import etree


DOCS_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
PRIMER_DOCX = SCRIPT_DIR / "primer.docx"

_NUM_ID_COUNTER = [1]
_CURRENT_NUM_ID = None
_HEAD_NUMS = [0, 0, 0, 0, 0, 0]
_BOOKMARK_ID = [0]
_MD_ANCHORS = {}
_CUR_MD = None
_HAS_MD_ANCHOR = False
_MANUAL_HEADING_NUMS = False

# Matches titles that already carry manual numbering like "1.1. ", "2. " or "Часть 1".
_MANUAL_NUM_RE = re.compile(r'^(?:Часть\s+)?(\d+(?:\.\d+)*)\.?\s')


def _reset_numbering():
    global _CURRENT_NUM_ID
    _CURRENT_NUM_ID = None


def _ensure_num_id(doc: Document) -> int:
    global _CURRENT_NUM_ID
    if _CURRENT_NUM_ID is None:
        _CURRENT_NUM_ID = _new_num_id(doc)
    return _CURRENT_NUM_ID


def _ensure_heading_styles(doc: Document, max_level: int = 6):
    existing = {s.name: s for s in doc.styles}
    for lvl in range(1, max_level + 1):
        name = f"Heading {lvl}"
        if name in existing:
            continue
        src_name = f"Heading {lvl - 1}"
        if src_name not in existing:
            continue
        new_style = copy.deepcopy(existing[src_name])
        name_el = new_style.element.find(qn("w:name"))
        if name_el is None:
            name_el = new_style.element.get_or_add_name()
        name_el.set(qn("w:val"), name.lower())
        doc.styles.element.append(new_style._element)
        existing[name] = new_style


def _fresh_abstract_num(numbering) -> int:
    for a in numbering.findall(qn("w:abstractNum")):
        if a.get(qn("w:abstractNumId")) == "1":
            return 1
    raise RuntimeError("abstractNum 1 not found in numbering.xml")


def _init_numbering(doc: Document):
    global _NUM_ID_COUNTER
    num_part = doc.part.numbering_part
    numbering = num_part._element
    existing_ids = [int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num")) if n.get(qn("w:numId"))]
    _NUM_ID_COUNTER[0] = max(existing_ids, default=0) + 1


def _new_num_id(doc: Document) -> int:
    global _NUM_ID_COUNTER
    num_part = doc.part.numbering_part
    numbering = num_part._element
    num_id = _NUM_ID_COUNTER[0]
    _NUM_ID_COUNTER[0] += 1
    abstract_id = _fresh_abstract_num(numbering)
    num_elem = parse_xml(f'''<w:num {nsdecls("w")} w:numId="{num_id}">
        <w:abstractNumId w:val="{abstract_id}"/>
        <w:lvlOverride w:ilvl="0">
            <w:startOverride w:val="1"/>
        </w:lvlOverride>
    </w:num>''')
    numbering.append(num_elem)
    return num_id


def _apply_numpr(p, num_id: str, ilvl: str = "0"):
    pPr = p._element.find(qn("w:pPr"))
    if pPr is None:
        pPr = parse_xml(f'<w:pPr {nsdecls("w")}/>')
        p._element.insert(0, pPr)
    numPr = pPr.find(qn("w:numPr"))
    if numPr is None:
        numPr = parse_xml(f'<w:numPr {nsdecls("w")}/>')
        pStyle = pPr.find(qn("w:pStyle"))
        if pStyle is not None:
            pStyle.addnext(numPr)
        else:
            pPr.insert(0, numPr)
    numIdFound = numPr.find(qn("w:numId"))
    if numIdFound is not None:
        numIdFound.set(qn("w:val"), num_id)
    else:
        numPr.append(parse_xml(f'<w:numId {nsdecls("w")} w:val="{num_id}"/>'))
    ilvlFound = numPr.find(qn("w:ilvl"))
    if ilvlFound is not None:
        ilvlFound.set(qn("w:val"), ilvl)
    else:
        numPr.append(parse_xml(f'<w:ilvl {nsdecls("w")} w:val="{ilvl}"/>'))


def _add_numbered_paragraph(doc: Document, text: str, num_id: int, md_rel="", fig_cnt=None):
    p = doc.add_paragraph(style="Перечень нум")
    _apply_numpr(p, str(num_id))
    _inline(p, text, md_rel, fig_cnt)
    return p


def _resolve_image(src: str, md_rel: str) -> Path | None:
    for c in [DOCS_ROOT / src, DOCS_ROOT / md_rel / src, DOCS_ROOT / md_rel / "assets" / src]:
        if c.exists():
            return c
    return None


def _resolve_md_target(src: str, md_rel: str) -> str | None:
    for base in [DOCS_ROOT / md_rel, DOCS_ROOT]:
        p = (base / src).resolve()
        if p.exists() and p.name.endswith(".md"):
            return str(p)
    return None


_PAGE_TEXT_W_IN = 6.3


def _attr_width(text: str) -> float | None:
    m = re.search(r'width="([0-9.]+)(%|px)"', text or "")
    if not m:
        return None
    v = float(m.group(1))
    if m.group(2) == "%":
        return _PAGE_TEXT_W_IN * v / 100.0
    return v / 96.0


def _add_img(par, path: Path, width_inches: float = 5.5):
    try:
        par.add_run().add_picture(str(path), width=Inches(width_inches))
    except Exception as e:
        r = par.add_run(f"[Image: {path.name} - {e}]")
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)


def _row_cant_split(row):
    """Prevent a table row from splitting across pages."""
    trPr = row._tr.get_or_add_trPr()
    cant = trPr.find(qn("w:cantSplit"))
    if cant is None:
        trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))


def _row_keep_next(row):
    """Keep the row on the same page as the following row."""
    for cell in row.cells:
        for p in cell.paragraphs:
            p.paragraph_format.keep_with_next = True


def _table_keep_header_with_rows(t):
    """Keep the header and at least 3 rows on the same page."""
    for ri, row in enumerate(t.rows):
        _row_cant_split(row)
        # keep_next on the header and the next two rows, so the header
        # stays on the same page as at least 3 rows in total.
        if ri < 3 and ri < len(t.rows) - 1:
            _row_keep_next(row)


def _add_run(par, text, bold=False, italic=False, size=None, color=None):
    r = par.add_run(text)
    r.bold = bold
    r.italic = italic
    if size:
        r.font.size = size
    if color:
        r.font.color.rgb = color
    return r


def _hyperlink_run(par, text, bookmark):
    run = par.add_run(text)
    try:
        run.style = run.part.document.styles["Hyperlink"]
    except Exception:
        run.font.color.rgb = RGBColor(0x05, 0x63, 0xFF)
        run.font.underline = True
    R = run._element

    def _r_with(inner_xml):
        return parse_xml(f'<w:r {nsdecls("w")}>{inner_xml}</w:r>')

    fld_begin = _r_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
    instr = _r_with(f'<w:instrText {nsdecls("w")} xml:space="preserve"> HYPERLINK \\l "{bookmark}" </w:instrText>')
    fld_sep = _r_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>')
    fld_end = _r_with(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
    for el in (fld_begin, instr, fld_sep):
        R.addprevious(el)
    R.addnext(fld_end)
    return run


def _add_bookmark(par, name):
    _BOOKMARK_ID[0] += 1
    start = parse_xml(f'<w:bookmarkStart {nsdecls("w")} w:id="{_BOOKMARK_ID[0]}" w:name="{name}"/>')
    end = parse_xml(f'<w:bookmarkEnd {nsdecls("w")} w:id="{_BOOKMARK_ID[0]}"/>')
    pPr = par._element.find(qn("w:pPr"))
    if pPr is not None and len(par._element) > 1:
        par._element.insert(1, start)
    else:
        par._element.insert(0, start)
    par._element.append(end)


def _xref_slug(path: str) -> str:
    return "xref_" + re.sub(r"[^A-Za-z0-9_]", "_", path)[-34:]


def _inline_img(par, part, md_rel, fig_cnt, bold=False):
    m = re.match(r'!\[([^\]]*)\]\(([^)\s"]+)(?:\s+"[^"]*")?\)', part)
    if not m:
        _add_run(par, part, bold=bold)
        return
    alt, src = m.group(1), m.group(2)
    ip = _resolve_image(src, md_rel)
    w = _attr_width(part)
    if ip:
        par.add_run().add_picture(str(ip), width=Inches(w or 1.2))
    else:
        _add_run(par, alt, size=Pt(9), color=RGBColor(0xCC, 0, 0), bold=bold)


def _inline(par, text, md_rel="", fig_cnt=None):
    segs = re.split(r'\s*<br\s*/?>\s*', text, flags=re.IGNORECASE)
    for si, seg in enumerate(segs):
        if si > 0:
            run = par.add_run()
            run._element.append(parse_xml(f'<w:br {nsdecls("w")}/>'))
        parts = re.split(
            r'(\*\*.*?\*\*|\*.*?\*|`.*?`|!\[[^\]]*\]\([^)\s"]+(?:\s+"[^"]*")?\)(?:\s*\{[^}]*\})?|\[[^\]]*\]\([^)]*\))',
            seg,
        )
        for part in parts:
            if part.startswith("**") and part.endswith("**"):
                _inline_bold(par, part[2:-2], md_rel, fig_cnt)
            elif part.startswith("*") and part.endswith("*"):
                _add_run(par, part[1:-1], italic=True)
            elif part.startswith("`") and part.endswith("`"):
                r = _add_run(par, part[1:-1], size=Pt(10))
                r.font.name = "Courier New"
            elif part.startswith("![") and "](" in part:
                _inline_img(par, part, md_rel, fig_cnt)
            elif part.startswith("[") and "](" in part:
                _inline_link(par, part, md_rel, bold=False)
            else:
                _add_run(par, part)


def _inline_bold(par, text, md_rel, fig_cnt):
    for sub in re.split(r'(!?\[[^\]]*\]\([^)]*\)(?:\s*\{[^}]*\})?)', text):
        if sub.startswith("![") and "](" in sub:
            _inline_img(par, sub, md_rel, fig_cnt, bold=True)
        elif sub.startswith("[") and "](" in sub:
            _inline_link(par, sub, md_rel, bold=True)
        else:
            _add_run(par, sub, bold=True)


def _inline_link(par, part, md_rel, bold):
    m = re.match(r'\[([^\]]*)\]\(([^)]*)\)', part)
    if not m:
        _add_run(par, part, bold=bold)
        return
    label, href = m.group(1), m.group(2).strip()
    if href.endswith(".md") or ".md#" in href:
        target = _resolve_md_target(href.split("#")[0].strip(), md_rel)
        anchor = href.split("#")[1] if "#" in href else ""
    else:
        target = None
        anchor = ""
    if target and target in _MD_ANCHORS:
        num = _MD_ANCHORS[target]
        for tok in re.split(r'(\*.*?\*|`.*?`)', label):
            if tok.startswith("*") and tok.endswith("*"):
                _add_run(par, tok[1:-1], bold=True)
            else:
                _add_run(par, tok, bold=bold)
        if num:
            _add_run(par, " (см. п. ")
            _hyperlink_run(par, num, _xref_slug(target))
            _add_run(par, ")")
    else:
        _add_run(par, label, bold=bold)


def _clean(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<a\s+id="[^"]*">\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</a>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*\{#[^}]+\}\s*', '', text)
    return text.strip()


def _prev_heading_level(doc):
    body = doc.element.body
    for el in reversed(body):
        if el.tag == qn("w:p"):
            pPr = el.find(qn("w:pPr"))
            if pPr is None:
                continue
            ps = pPr.find(qn("w:pStyle"))
            if ps is None:
                return None
            val = ps.get(qn("w:val"))
            return int(val) if val.isdigit() else None
        if el.tag == qn("w:sectPr"):
            continue
        return None
    return None


def _heading(doc, title, level, numbered=True):
    global _HEAD_NUMS, _MANUAL_HEADING_NUMS
    title = _clean(title)
    page_break = False
    num = ""
    if numbered:
        level = max(1, min(level, 6))
        if _MANUAL_HEADING_NUMS:
            # The markdown already carries manual numbering ("1.1. ...", "Часть 1 ...").
            # Keep titles as-is and don't prepend automatic numbers.
            page_break = level <= 2
        else:
            _HEAD_NUMS[level - 1] += 1
            for li in range(level, 6):
                _HEAD_NUMS[li] = 0
            first = next((i for i in range(level) if _HEAD_NUMS[i]), level - 1)
            num = ".".join(str(_HEAD_NUMS[i]) for i in range(first, level))
            title = f"{num} {title}"
            page_break = len(num.split(".")) <= 2
        prev = _prev_heading_level(doc)
        if page_break and prev == level - 1:
            page_break = False
    h = doc.add_heading(title, level=level)
    if page_break:
        h.paragraph_format.page_break_before = True
    pPr = h._element.get_or_add_pPr()
    ol = pPr.find(qn("w:outlineLvl"))
    if ol is None:
        ol = parse_xml(f'<w:outlineLvl {nsdecls("w")} w:val="{level - 1}"/>')
        pPr.append(ol)
    else:
        ol.set(qn("w:val"), str(level - 1))
    global _CUR_MD, _HAS_MD_ANCHOR
    if _CUR_MD and not _HAS_MD_ANCHOR:
        _HAS_MD_ANCHOR = True
        full = _CUR_MD if isinstance(_CUR_MD, str) else str(_CUR_MD)
        _add_bookmark(h, _xref_slug(full))
        _MD_ANCHORS[full] = num
    _reset_numbering()
    return h


def _page_break(doc):
    p = doc.add_paragraph()
    p.add_run()._element.append(parse_xml(f'<w:br {nsdecls("w")} w:type="page"/>'))


def _enable_field_updates(doc):
    settings = doc.settings.element
    uf = settings.find(qn("w:updateFields"))
    if uf is None:
        settings.insert(0, parse_xml(f'<w:updateFields {nsdecls("w")} w:val="true"/>'))
    else:
        uf.set(qn("w:val"), "true")


def _find_rel_id(doc, target_substr: str) -> str | None:
    for rel in doc.part.rels.values():
        if target_substr in rel.target_ref:
            return rel.rId
    return None


def _capture_content_section_refs(doc) -> tuple[str | None, str | None]:
    """Capture header/footer references of the template's body-final section.

    These parts define the kolontituly of the content pages in the template.
    The references must be read before add_section() clones and strips the
    body-final sectPr."""
    body_final = doc.element.body.find(qn("w:sectPr"))
    if body_final is None:
        return None, None
    hr = body_final.find(qn("w:headerReference"))
    fr = body_final.find(qn("w:footerReference"))
    return (
        hr.get(qn("r:id")) if hr is not None else None,
        fr.get(qn("r:id")) if fr is not None else None,
    )


def _set_footer_ref(section, rId: str, footer_type: str = "default"):
    sectPr = section._sectPr
    for ref in list(sectPr.findall(qn("w:footerReference"))):
        if ref.get(qn("w:type")) == footer_type:
            sectPr.remove(ref)
    ref = parse_xml(
        f'<w:footerReference {nsdecls("w")} {nsdecls("r")} w:type="{footer_type}" r:id="{rId}"/>'
    )
    sectPr.insert(0, ref)


def _set_header_ref(section, rId: str, header_type: str = "default"):
    sectPr = section._sectPr
    for ref in list(sectPr.findall(qn("w:headerReference"))):
        if ref.get(qn("w:type")) == header_type:
            sectPr.remove(ref)
    ref = parse_xml(
        f'<w:headerReference {nsdecls("w")} {nsdecls("r")} w:type="{header_type}" r:id="{rId}"/>'
    )
    sectPr.insert(0, ref)


def _update_header_text(header_part, product_name: str):
    updated = False
    for sdt in header_part._element.iter(qn("w:sdt")):
        alias_el = sdt.find(qn("w:sdtPr"))
        if alias_el is None:
            continue
        alias = alias_el.find(qn("w:alias"))
        if alias is None or alias.get(qn("w:val")) != "Название":
            continue
        content = sdt.find(qn("w:sdtContent"))
        if content is None:
            continue
        for t_el in content.iter(qn("w:t")):
            t_el.text = product_name
        updated = True
    if not updated:
        for p in list(header_part.paragraphs):
            p._element.getparent().remove(p._element)
        for t in list(header_part.tables):
            t._element.getparent().remove(t._element)
        p = header_part.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_run(p, product_name, size=Pt(11), color=RGBColor(0x7F, 0x7F, 0x7F))


def _add_footer(doc, product_name: str, content_header_rid=None, content_footer_rid=None):
    """Set up headers/footers for all sections.

    The title section (idx 0) gets the template's empty footer and no header.
    Content sections reuse the template's own header/footer parts captured from
    the body-final sectPr of the source document, so the template layout
    (page-number fields, borders, copyright) is preserved. Only the product
    name placeholder in the header is replaced.
    """
    for idx, section in enumerate(doc.sections):
        if idx == 0:
            rId = _find_rel_id(doc, "footer1.xml")
            if rId:
                _set_footer_ref(section, rId, "default")
            for ref in list(section._sectPr.findall(qn("w:headerReference"))):
                section._sectPr.remove(ref)
            continue

        if content_header_rid:
            _set_header_ref(section, content_header_rid, "default")
            try:
                _update_header_text(section.header, product_name)
            except Exception:
                pass
        else:
            header_rId = _find_rel_id(doc, "header1.xml")
            if header_rId:
                _set_header_ref(section, header_rId, "default")
            header = section.header
            header.is_linked_to_previous = False
            _update_header_text(header, product_name)

        if content_footer_rid:
            _set_footer_ref(section, content_footer_rid, "default")
        else:
            footer = section.footer
            footer.is_linked_to_previous = False
            for p in list(footer.paragraphs):
                p._element.getparent().remove(p._element)
            for t in list(footer.tables):
                t._element.getparent().remove(t._element)
            p = footer.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _add_run(p, f"©Группа компаний «Цифра», {datetime.date.today().year}. Все права защищены.",
                     size=Pt(9), color=RGBColor(0x66, 0x66, 0x66))


# --- admonitions ---
# The template renders notes/warnings as plain paragraphs with a bold prefix
# (e.g. "Примечание. …", "ВНИМАНИЕ! …"). Follow that convention instead of
# drawing colored boxes with hardcoded colors.

_ADMON_LABEL = {
    "note": "Примечание.",
    "info": "Сведения.",
    "tip": "Совет.",
    "warning": "ВНИМАНИЕ!",
    "danger": "Опасно!",
    "question": "Вопрос.",
}


def _admon_label(kind: str) -> str:
    return _ADMON_LABEL.get(kind, "Примечание.")


def _add_admonition(doc, kind: str, title: str):
    p = doc.add_paragraph()
    _add_run(p, title, bold=True)
    return p


# --- render markdown ---

def _add_caption(doc, text: str, style_name: str):
    """Add a figure/table caption using a template paragraph style."""
    pc = doc.add_paragraph()
    try:
        pc.style = style_name
    except Exception:
        pass
    _add_run(pc, text)
    return pc


def _template_header_fill(doc) -> str | None:
    """Read the header-row fill colour from the template's table style
    ('Цифра', used for the revision table), instead of hardcoding one."""
    try:
        style = doc.styles["Цифра"]
    except KeyError:
        return None
    for tbl_style_pr in style.element.iter(qn("w:tblStylePr")):
        if tbl_style_pr.get(qn("w:type")) != "firstRow":
            continue
        for shd in tbl_style_pr.iter(qn("w:shd")):
            return shd.get(qn("w:fill"))
    return None


# --- pymdownx snippet expansion ---

_SNIPPET_RE = re.compile(r'^--8<--\s+"([^"]+)"\s*$')


def _expand_snippets(text: str, base: Path, _seen: set | None = None) -> str:
    """Expand pymdownx snippet directives (``--8<-- "file.md"``) inline.

    Snippet filenames are resolved the same way ``pymdownx.snippets`` does:
    first relative to the current markdown file's directory, then against the
    docs root and the ``docs/snippets`` folder. Expansion is recursive and
    cycle-safe, so snippets that reference further snippets are expanded too.
    """
    if _seen is None:
        _seen = set()
    out_lines = []
    for line in text.split("\n"):
        m = _SNIPPET_RE.match(line)
        if not m:
            out_lines.append(line)
            continue
        name = m.group(1).strip()
        found = None
        for cand in (
            base / name,
            DOCS_ROOT / name,
            DOCS_ROOT / "snippets" / name,
            DOCS_ROOT / "docs" / name,
            DOCS_ROOT / "docs" / "snippets" / name,
        ):
            try:
                cand = cand.resolve()
            except OSError:
                continue
            if cand.exists():
                found = cand
                break
        if found is None:
            out_lines.append(f"*[Сниппет не найден: {name}]*")
            continue
        if found in _seen:
            out_lines.append(f"*[Рекурсивный сниппет: {name}]*")
            continue
        _seen.add(found)
        try:
            snippet = found.read_text(encoding="utf-8")
            out_lines.append(_expand_snippets(snippet, found.parent, _seen))
        finally:
            _seen.discard(found)
    return "\n".join(out_lines)


def _render_md(md_path: Path, heading_base: int, doc, fig_cnt, tbl_cnt):
    global _CUR_MD, _HAS_MD_ANCHOR
    if not md_path.exists():
        p = doc.add_paragraph(f"[File not found: {md_path}]")
        p.runs[0].font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
        return
    lines = md_path.read_text(encoding="utf-8").split("\n")
    _render_lines(lines, md_path, heading_base, doc, fig_cnt, tbl_cnt, skip_first_h1=True)
    _CUR_MD = None
    _HAS_MD_ANCHOR = False


def _render_lines(lines, md_path: Path, heading_base: int, doc, fig_cnt, tbl_cnt, skip_first_h1: bool):
    global _CUR_MD, _HAS_MD_ANCHOR
    _CUR_MD = str(md_path.resolve())
    _HAS_MD_ANCHOR = False
    lines = _expand_snippets("\n".join(lines), md_path).split("\n")
    first_h1 = skip_first_h1
    md_rel = str(md_path.parent.relative_to(DOCS_ROOT))
    i = 0
    in_comment = False
    while i < len(lines):
        line = lines[i]
        if in_comment:
            if "-->" in line:
                in_comment = False
                i += 1
                continue
            i += 1
            continue
        if "<!--" in line and "-->" not in line:
            if not re.search(r'<!--.*-->', line):
                in_comment = True
                i += 1
                continue
        if line.strip() == "{%":
            j = i + 1
            inc_lines = []
            while j < len(lines) and lines[j].strip() != "%}":
                inc_lines.append(lines[j])
                j += 1
            if j < len(lines):
                inc_text = "\n".join(inc_lines)
                inc_match = re.search(r'include-markdown\s+"([^"]+)"', inc_text)
                if inc_match:
                    inc_path = inc_match.group(1)
                    start = re.search(r'start="([^"]+)"', inc_text)
                    end = re.search(r'end="([^"]+)"', inc_text)
                    inc_candidates = [
                        md_path.parent / inc_path,
                        DOCS_ROOT / inc_path,
                    ]
                    inc_file = None
                    for c in inc_candidates:
                        if c.exists():
                            inc_file = c
                            break
                    if inc_file:
                        inc_content = inc_file.read_text(encoding="utf-8")
                        if start and start.group(1) in inc_content:
                            inc_content = inc_content.split(start.group(1), 1)[1]
                        if end and end.group(1) in inc_content:
                            inc_content = inc_content.split(end.group(1), 1)[0]
                        _render_lines(inc_content.split("\n"), inc_file, heading_base, doc, fig_cnt, tbl_cnt, skip_first_h1=False)
                    else:
                        p = doc.add_paragraph(f"[Include not found: {inc_path}]")
                        p.runs[0].font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
                i = j + 1
                continue
        if re.match(r'^<a\s+id=', line, re.IGNORECASE):
            i += 1
            continue
        hm = re.match(r'^(#{1,6})\s+(.*)', line)
        if hm:
            lvl = len(hm.group(1))
            title = _clean(hm.group(2))
            if lvl == 1 and first_h1:
                first_h1 = False
                i += 1
                continue
            if title == "Содержание":
                i += 1
                while i < len(lines):
                    nhm = re.match(r'^(#{1,6})\s+', lines[i])
                    if nhm and len(nhm.group(1)) <= lvl:
                        break
                    i += 1
                continue
            new_lvl = min(lvl + heading_base - 1, 6)
            _heading(doc, title, new_lvl)
            i += 1
            continue
        img = re.match(r'!\[([^\]]*)\]\(([^)\s"]+)(?:\s+"[^"]*")?\s*\)(?:\s*\{[^}]*\})*\s*$', line.strip())
        if img:
            alt, src = img.group(1), img.group(2).strip()
            has_caption = i + 1 < len(lines) and re.match(r'^///\s*caption', lines[i + 1].strip(), re.IGNORECASE)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if has_caption:
                # Keep the image on the same page as its caption.
                p.paragraph_format.keep_with_next = True
            ip = _resolve_image(src, md_rel)
            w = _attr_width(line.strip())
            if ip:
                _add_img(p, ip, w or 5.5)
            else:
                _add_run(p, f"[Image not found: {src}]", size=Pt(9), color=RGBColor(0xCC, 0, 0))
            if has_caption:
                cap = []
                j = i + 2
                while j < len(lines) and not lines[j].lstrip().startswith("///"):
                    cap.append(lines[j].strip())
                    j += 1
                ct = " ".join(cap)
                fig_cnt[0] += 1
                _add_caption(doc, f"Рисунок {fig_cnt[0]} - {ct or alt}", "Название рисунка")
                i = j + 1
            else:
                i += 1
            continue
        adm = re.match(r'^(\s*)(!{3}|\?{3}\+?)\s+([\w-]+)\s*(.*)', line, re.IGNORECASE)
        if adm:
            adm_indent = len(adm.group(1))
            adm_marker = adm.group(2)
            kind = adm.group(3).lower()
            resto = adm.group(4).strip()
            qt = re.match(r'^"([^"]*)"', resto)
            title = qt.group(1).strip() if qt else (resto or _admon_label(kind))
            if adm_marker.startswith("?") and adm_indent > 0:
                pass
            else:
                clines = []
                j = i + 1
                while j < len(lines):
                    s = lines[j]
                    if s.strip() and len(s) - len(s.lstrip()) <= adm_indent:
                        break
                    if s.startswith("    ") or not s.strip():
                        clines.append(s)
                        j += 1
                    else:
                        break
                if kind == "warning":
                    _render_warning_table(
                        doc,
                        qt.group(1).strip() if qt else "",
                        clines,
                        md_rel,
                        fig_cnt,
                    )
                    i = j
                    continue
                p = _add_admonition(doc, kind, title)
                first = True
                for cl in clines:
                    ct = cl.strip()
                    if not ct:
                        continue
                    if first:
                        p.add_run(" ")
                        _inline(p, ct, md_rel, fig_cnt)
                        first = False
                    else:
                        p2 = doc.add_paragraph()
                        p2.paragraph_format.space_after = Pt(2)
                        _inline(p2, ct, md_rel, fig_cnt)
                i = j
                continue
        if "|" in line and re.match(r'^\s*\|', line):
            rows = []
            while i < len(lines) and "|" in lines[i]:
                s = lines[i].strip()
                if not s.startswith("|"):
                    break
                cells = [c.strip() for c in s.strip("|").split("|")]
                if re.match(r'^[\s:|:-]+$', s.replace("|", "").strip()):
                    i += 1
                    continue
                rows.append(cells)
                i += 1
            cap_text = ""
            if i < len(lines) and re.match(r'^///\s*caption', lines[i].strip(), re.IGNORECASE):
                cap = []
                i += 1
                while i < len(lines) and not lines[i].lstrip().startswith("///"):
                    cap.append(lines[i].strip())
                    i += 1
                cap_text = " ".join(cap)
                if i < len(lines) and lines[i].lstrip().startswith("///"):
                    i += 1
                if cap_text:
                    tbl_cnt[0] += 1
                    _add_caption(doc, f"Таблица {tbl_cnt[0]} - {cap_text}", "Название таблицы")
            if rows:
                nc = max(len(r) for r in rows)
                t = doc.add_table(rows=len(rows), cols=nc)
                t.style = "Table Grid"
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                hdr_fill = _template_header_fill(doc)
                for ri, rc in enumerate(rows):
                    for ci in range(nc):
                        cell = t.cell(ri, ci)
                        cell.text = ""
                        _inline(cell.paragraphs[0], rc[ci] if ci < len(rc) else "")
                        if ri == 0:
                            if hdr_fill:
                                sh = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hdr_fill}"/>')
                                cell._tc.get_or_add_tcPr().append(sh)
                            for r in cell.paragraphs[0].runs:
                                r.bold = True
                _table_keep_header_with_rows(t)
            continue
        if not line.strip():
            i += 1
            continue
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            p = doc.add_paragraph(style="Перечень марк")
            _inline(p, re.sub(r'^[-*]\s+', '', line.strip()), md_rel, fig_cnt)
            i += 1
            continue
        nm = re.match(r'^\s*(\d+)\.\s+(.*)', line)
        if nm:
            if nm.group(1) == "1":
                _reset_numbering()
            _add_numbered_paragraph(doc, nm.group(2), _ensure_num_id(doc), md_rel, fig_cnt)
            i += 1
            continue
        p = doc.add_paragraph()
        _inline(p, _clean(line.strip()), md_rel, fig_cnt)
        i += 1


# --- extract headings for TOC ---

def _extract_headings(md_path: Path) -> list[tuple[int, str]]:
    """Scan the markdown file and return (level, title) for every heading."""
    if not md_path.exists():
        return []
    headings = []
    text = _expand_snippets(md_path.read_text(encoding="utf-8"), md_path)
    in_comment = False
    skip_toc = False
    toc_level = 0
    for line in text.split("\n"):
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line and "-->" not in line:
            if not re.search(r'<!--.*-->', line):
                in_comment = True
            continue
        hm = re.match(r'^(#{1,6})\s+(.*)', line)
        if hm:
            lvl = len(hm.group(1))
            title = _clean(hm.group(2))
            if title == "Содержание":
                skip_toc = True
                toc_level = lvl
                continue
            if skip_toc:
                if lvl <= toc_level:
                    skip_toc = False
                else:
                    continue
            headings.append((lvl, title))
    return headings


def _detect_manual_numbering(md_path: Path) -> bool:
    """Return True if the document's headings already carry manual numbers
    ("1.1. ...", "Часть 1 ..."). In that case automatic numbering is disabled."""
    if not md_path.exists():
        return False
    text = _expand_snippets(md_path.read_text(encoding="utf-8"), md_path)
    for line in text.split("\n"):
        hm = re.match(r'^(#{2,6})\s+(.*)', line)
        if not hm:
            continue
        title = _clean(hm.group(2))
        if _MANUAL_NUM_RE.match(title):
            return True
    return False


# --- title page / revision / warning ---

_TITLE_ROW_PLAN = (500, 3900, 2200, 850, 850, 700, 850)


def _fit_title_page(doc):
    """Keep the template's title table on one page when LibreOffice renders
    the DOCX to PDF. LibreOffice grows rows beyond the declared minimums
    (the logo is taller than its row), which pushes the version row onto a
    second page. Force exact row heights sized to fit the printable area."""
    if not doc.tables:
        return
    tbl = doc.tables[0]._tbl
    for i, tr in enumerate(tbl.findall(qn("w:tr"))[: len(_TITLE_ROW_PLAN)]):
        trPr = tr.find(qn("w:trPr"))
        if trPr is None:
            trPr = parse_xml(f'<w:trPr {nsdecls("w")}/>')
            tr.insert(0, trPr)
        trHeight = trPr.find(qn("w:trHeight"))
        if trHeight is None:
            trHeight = parse_xml(f'<w:trHeight {nsdecls("w")}/>')
            trPr.append(trHeight)
        trHeight.set(qn("w:val"), str(_TITLE_ROW_PLAN[i]))
        trHeight.set(qn("w:hRule"), "exact")


def _title_page(doc, product_name):
    if not doc.tables:
        return
    t = doc.tables[0]
    for sdt in t._element.iter(qn("w:sdt")):
        alias_el = sdt.find(qn("w:sdtPr"))
        if alias_el is None:
            continue
        alias = alias_el.find(qn("w:alias"))
        if alias is None or alias.get(qn("w:val")) != "Название":
            continue
        content = sdt.find(qn("w:sdtContent"))
        if content is None:
            continue
        for t_el in content.iter(qn("w:t")):
            t_el.text = product_name
        break
    else:
        try:
            h1 = doc.styles["Heading 1"]
            size = h1.font.size
            color = h1.font.color.rgb
        except (KeyError, ValueError):
            size, color = None, None
        size = size or Pt(28)
        for row_idx in (2, 3):
            if row_idx >= len(t.rows):
                continue
            for p in t.rows[row_idx].cells[0].paragraphs:
                if p.text.strip():
                    p.clear()
                    _add_run(p, product_name, size=size, color=color)
                    return


def _update_revision_date(rev_tbl):
    """Refresh the 'Дата' column of the template's revision table without
    rebuilding the table (text/shape of the copy stays as it is in the
    template)."""
    if len(rev_tbl.rows) < 2 or len(rev_tbl.rows[1].cells) < 2:
        return
    cell = rev_tbl.rows[1].cells[1]
    cell.text = ""
    cell.paragraphs[0].add_run(datetime.date.today().strftime("%d.%m.%Y"))


def _revision_fallback(doc):
    """Only used when the template has no revision table of its own."""
    t = doc.add_table(rows=2, cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_fill = _template_header_fill(doc)
    for ci, h in enumerate(["Версия", "Дата", "Автор", "Описание"]):
        c = t.cell(0, ci)
        c.text = ""
        _add_run(c.paragraphs[0], h, bold=True)
        if hdr_fill:
            c._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hdr_fill}"/>'))
    today = datetime.date.today().strftime("%d.%m.%Y")
    for ci, d in enumerate([_latest_doc_version(), today, "Система", "Начальная версия документа"]):
        t.cell(1, ci).text = ""
        t.cell(1, ci).paragraphs[0].add_run(d)


def _warning_fallback(doc):
    """Only used when the template has no 'Предупреждение' table of its own."""
    t = doc.add_table(rows=2, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c0 = t.cell(0, 0)
    c0.text = ""
    _add_run(c0.paragraphs[0], "Предупреждение", bold=True, size=Pt(12),
             color=RGBColor(0xCC, 0, 0))
    c1 = t.cell(1, 0)
    c1.text = ""
    _add_run(c1.paragraphs[0],
             "Данный документ является интеллектуальной собственностью. "
             "Все права защищены. Копирование и распространение без разрешения запрещено.",
             size=Pt(10))


def _find_revision_table(doc):
    for t in doc.tables:
        if t.rows and t.rows[0].cells and t.rows[0].cells[0].text.strip() == "Версия":
            return t
    return None


def _latest_doc_version() -> str:
    """Return the latest version from docs/release-notes.md (first ## X.Y.Z)."""
    m = re.search(r"^##\s+(\d+\.\d+\.\d+)",
                  (DOCS_ROOT / "docs" / "release-notes.md").read_text(encoding="utf-8"),
                  re.M)
    return m.group(1) if m else "1.0"


def _set_doc_version(doc, version: str):
    """Replace the placeholder version string across the document.

    Updates the 'Аннотация' SDT (title page + headers), the cover-page
    custom XML property, and the revision table's version cell.
    """
    if version == "1.0":
        return
    # Body SDTs (title page, headers)
    for sdt in doc.element.body.iter(qn("w:sdt")):
        _rewrite_sdt_text(sdt, "Аннотация", version)
    # Header parts (right side of running header)
    for section in doc.sections:
        for part in (section.header, section.first_page_header, section.even_page_header):
            if part is None:
                continue
            for sdt in part._element.iter(qn("w:sdt")):
                _rewrite_sdt_text(sdt, "Аннотация", version)
    # Cover-page custom XML property
    try:
        for part in doc.part.package.parts:
            if getattr(part, "partname", "") != "/customXml/item1.xml":
                continue
            from lxml import etree as _etree
            root = _etree.fromstring(part.blob)
            ns = {"ns0": "http://schemas.microsoft.com/office/2006/coverPageProps"}
            abstract = root.find("ns0:Abstract", ns)
            if abstract is not None and "1.0" in (abstract.text or ""):
                abstract.text = abstract.text.replace("1.0", version)
                part._blob = _etree.tostring(root, xml_declaration=True,
                                             encoding="UTF-8", standalone="yes")
    except Exception:
        pass
    # Revision table – first data row, version column
    rev = _find_revision_table(doc)
    if rev and len(rev.rows) >= 2 and len(rev.rows[1].cells) >= 1:
        cell = rev.rows[1].cells[0]
        if cell.text.strip() == "1.0":
            cell.text = ""
            cell.paragraphs[0].add_run(version)


def _rewrite_sdt_text(sdt, alias_name: str, version: str):
    """Replace the version inside an SDT whose alias equals ``alias_name``.

    The placeholder text can be split across several runs (e.g. the title
    page stores it as "Версия документа – 1." + "0"), so the runs are
    joined, the version is replaced, and the result is written back into
    the first run.
    """
    alias_el = sdt.find(".//" + qn("w:alias"))
    if alias_el is None or alias_el.get(qn("w:val")) != alias_name:
        return
    content = sdt.find(qn("w:sdtContent"))
    if content is None:
        return
    t_els = list(content.iter(qn("w:t")))
    if not t_els:
        return
    old = "".join(t.text or "" for t in t_els)
    if "1.0" not in old:
        return
    new = old.replace("1.0", version)
    t_els[0].text = new
    t_els[0].set(qn("xml:space"), "preserve")
    for t in t_els[1:]:
        t.text = ""


def _find_warning_table(doc):
    for t in doc.tables:
        if t.rows and t.rows[0].cells and t.rows[0].cells[0].text.strip() == "Предупреждение":
            return t
    return None


_WARNING_TPL_XML: str | None = None
_WARNING_TPL_LOADED = False


def _template_warning_xml() -> str | None:
    """Return the cached XML string of the template's 'Предупреждение' table,
    or ``None`` when the template lacks it.  Loaded once per process."""
    global _WARNING_TPL_XML, _WARNING_TPL_LOADED
    if not _WARNING_TPL_LOADED:
        _WARNING_TPL_LOADED = True
        try:
            tpl = Document(str(PRIMER_DOCX))
            tw = _find_warning_table(tpl)
            if tw is not None:
                _WARNING_TPL_XML = etree.tostring(tw._tbl, encoding="unicode")
        except Exception:
            pass
    return _WARNING_TPL_XML


def _render_warning_table(doc, title: str, clines: list[str], md_rel: str, fig_cnt: list[int]):
    """Insert a 'Предупреждение' table into *doc* whose XML structure comes
    from the template, filled with the real MD admonition content.

    The first row is the label (template header colour); the second row
    receives the admonition body text.  When *title* equals the default
    label 'Предупреждение' (i.e. no custom title in MD), the label cell
    text is left untouched.
    """
    xml = _template_warning_xml()
    if xml is None:
        _warning_fallback(doc)
        return

    el = parse_xml(xml)
    doc.element.body.find(qn("w:sectPr")).addprevious(el)
    from docx.table import Table
    t = Table(el, doc)
    if len(t.rows) < 2:
        return

    # Optionally replace the label when the MD source provides a custom title
    if title and title != "Предупреждение":
        label_cell = t.rows[0].cells[0]
        label_cell.text = ""
        run = label_cell.paragraphs[0].add_run(title)
        run.bold = True

    body_cell = t.rows[1].cells[0]
    body_cell.text = ""
    first = True
    for cl in clines:
        ct = cl.strip()
        if not ct:
            continue
        p = body_cell.paragraphs[0] if first else body_cell.add_paragraph()
        _inline(p, ct, md_rel, fig_cnt)
        first = False


def _find_toc_sdt(doc):
    for el in doc.element.body.iter(qn("w:sdt")):
        for it in el.iter(qn("w:instrText")):
            if it.text and it.text.strip().startswith("TOC"):
                return el
    return None


# --- TOC field ---

def _add_toc_field(doc):
    p = doc.add_paragraph()
    pPr = p._element.get_or_add_pPr()
    ps = parse_xml(f'<w:pStyle {nsdecls("w")} w:val="11"/>')
    pPr.insert(0, ps)
    r1 = p.add_run()
    r1._element.append(parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>'))
    r2 = p.add_run()
    r2._element.append(parse_xml(
        f'<w:instrText {nsdecls("w")} xml:space="preserve"> TOC \\o "2-4" \\h \\z \\u </w:instrText>'))
    r3 = p.add_run()
    r3._element.append(parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="separate"/>'))
    r4 = p.add_run()
    r4._element.append(parse_xml(f'<w:t {nsdecls("w")}>Щёлкните правой кнопкой → Обновить поле</w:t>'))
    r5 = p.add_run()
    r5._element.append(parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>'))
    return p


# --- TOC entries: real headings + page numbers ---

_HEADING_STYLE_IDS = ("1", "2", "3")


def _collect_heading_entries(doc):
    """Return [(level, text), ...] for every Heading 1-3 paragraph in the
    body, excluding the TOC field's own cached content (which lives inside
    the sdt). Heading text is exactly what is rendered in the body — numbers
    are already literal there ("1.1 Загрузка сотрудников")."""
    entries = []
    for p in doc.element.body.iter(qn("w:p")):
        if any(a.tag == qn("w:sdt") for a in p.iterancestors()):
            continue
        pPr = p.find(qn("w:pPr"))
        if pPr is None:
            continue
        st = pPr.find(qn("w:pStyle"))
        if st is None or st.get(qn("w:val")) not in _HEADING_STYLE_IDS:
            continue
        text = "".join(t.text or "" for t in p.iter(qn("w:t"))).strip()
        if text:
            entries.append((int(st.get(qn("w:val"))), text))
    return entries


def _rebuild_toc_entries(doc, toc_pages=None):
    """Replace the cached result of the template's TOC field with the real
    headings of this document.

    LibreOffice does not recompute TOC fields during ``--convert-to pdf`` —
    it renders the cached field result, which in the template contains the
    primer's example headings. So we write the correct entries ourselves.

    ``toc_pages`` maps heading text -> page number; the mkdocs hook obtains
    it from a first conversion pass. Without it the numbers are placeholders
    (Word still updates the field because ``w:updateFields`` is set, so the
    DOCX stays correct when opened in Word).
    """
    sdt = _find_toc_sdt(doc)
    if sdt is None:
        return []
    content = sdt.find(qn("w:sdtContent"))
    if content is None:
        return []
    paras = list(content.findall(qn("w:p")))
    if len(paras) < 3:
        return []

    # The outer TOC field is: paragraph with an instrText "TOC ..." (holds the
    # begin + separate fldChars and the first cached entry), then one paragraph
    # per cached entry (each carries its own PAGEREF field), then the final
    # paragraph holding the TOC field's trailing "end" fldChar.
    begin_p = None
    for p in paras:
        if any((it.text or "").strip().startswith("TOC") for it in p.iter(qn("w:instrText"))):
            begin_p = p
            break
    if begin_p is None:
        return []
    end_p = None
    for p in reversed(paras):
        if p is begin_p:
            break
        if "end" in [f.get(qn("w:fldCharType")) for f in p.iter(qn("w:fldChar"))]:
            end_p = p
            break
    if end_p is None:
        return []

    templates = []
    started = False
    for p in paras:
        if p is begin_p:
            started = True
            continue
        if p is end_p:
            break
        if started:
            templates.append(p)
    if not templates:
        return []
    template_entry = copy.deepcopy(templates[0])

    started = False
    for p in list(content.findall(qn("w:p"))):
        if p is begin_p:
            started = True
            continue
        if p is end_p:
            break
        if started:
            content.remove(p)

    # Drop the cached first entry glued inside begin_p after the 'separate'.
    for i, child in enumerate(list(begin_p)):
        if child.tag != qn("w:r"):
            continue
        if any(f.get(qn("w:fldCharType")) == "separate" for f in child.findall(qn("w:fldChar"))):
            for extra in list(begin_p)[i + 1:]:
                begin_p.remove(extra)
            break

    entries = _collect_heading_entries(doc)
    page_map = toc_pages or {}
    last = "1"
    for lvl, text in entries:
        p = copy.deepcopy(template_entry)
        for child in list(p):
            if child.tag != qn("w:pPr"):
                p.remove(child)
        pPr = p.find(qn("w:pPr"))
        if lvl > 1:
            ind = parse_xml(f'<w:ind {nsdecls("w")} w:left="{(lvl - 1) * 567}"/>')
            rPr = pPr.find(qn("w:rPr"))
            if rPr is not None:
                rPr.addprevious(ind)
            else:
                pPr.append(ind)
        page = page_map.get(text)
        if page is None:
            page = last
        last = str(page)
        r_text = parse_xml(
            f'<w:r {nsdecls("w")}><w:rPr><w:rStyle {nsdecls("w")} w:val="af0"/>'
            f'<w:noProof {nsdecls("w")}/></w:rPr>'
            f'<w:t {nsdecls("w")} xml:space="preserve">{_xml_escape(text)}</w:t></w:r>')
        r_tab = parse_xml(
            f'<w:r {nsdecls("w")}><w:rPr><w:noProof {nsdecls("w")}/>'
            f'<w:webHidden {nsdecls("w")}/></w:rPr><w:tab {nsdecls("w")}/></w:r>')
        r_num = parse_xml(
            f'<w:r {nsdecls("w")}><w:rPr><w:noProof {nsdecls("w")}/>'
            f'<w:webHidden {nsdecls("w")}/></w:rPr>'
            f'<w:t {nsdecls("w")} xml:space="preserve">{last}</w:t></w:r>')
        for rr in (r_text, r_tab, r_num):
            p.append(rr)
        end_p.addprevious(p)
    return entries


def _strip_heading_autonum(doc: Document):
    for s in doc.styles:
        if not s.name or not s.name.lower().startswith("heading"):
            continue
        pPr = s.element.find(qn("w:pPr"))
        if pPr is None:
            continue
        numPr = pPr.find(qn("w:numPr"))
        if numPr is not None:
            pPr.remove(numPr)


def _reset_global_counters():
    global _HEAD_NUMS, _NUM_ID_COUNTER, _CURRENT_NUM_ID, _BOOKMARK_ID, _MD_ANCHORS, _MANUAL_HEADING_NUMS
    _HEAD_NUMS = [0, 0, 0, 0, 0, 0]
    _NUM_ID_COUNTER = [1]
    _CURRENT_NUM_ID = None
    _BOOKMARK_ID = [0]
    _MD_ANCHORS = {}
    _MANUAL_HEADING_NUMS = False


def _fresh_doc() -> tuple[Document, list]:
    """Open the template and drop its example content, keeping only the
    structural elements: the title table, the 'Изменения в документе' heading
    with the revision table, and the TOC sdt.

    The template's 'Предупреждение' table is intentionally NOT preserved
    here: its text is only a fill-in sample and must not appear in generated
    documents. Its XML is cached separately (see ``_template_warning_xml``)
    and reused only when an MD admonition ``!!! warning`` is rendered.

    Returns (doc, kept_elements) where kept_elements are the front-matter
    blocks that should be placed into the content section after the title
    page. Everything else in the template body is removed.
    """
    doc = Document(str(PRIMER_DOCX))
    body = doc.element.body
    children = list(body)

    rev_heading = rev_tbl = toc_sdt = None

    # NOTE: use python-docx proxies (p.text / cell.text) for text detection:
    # raw `itertext()` on the template's runs returns duplicated text, because
    # of the parser artifact with w:lastRenderedPageBreak (a w:t child plus a
    # copy attached to the run).
    for p in doc.paragraphs:
        if p.text.strip() == "Изменения в документе":
            rev_heading = p._element
            break

    rev_tbl_obj = _find_revision_table(doc)
    if rev_tbl_obj is not None:
        rev_tbl = rev_tbl_obj._tbl

    for el in children:
        if el.tag != qn("w:sdt"):
            continue
        if any((it.text or "").strip().startswith("TOC") for it in el.iter(qn("w:instrText"))):
            toc_sdt = el
            break

    kept = [k for k in (rev_heading, rev_tbl, toc_sdt) if k is not None]

    for el in children:
        if el.tag == qn("w:sectPr"):
            continue
        if el is children[0] or el in kept:
            continue
        body.remove(el)

    return doc, kept


def _move_to_body_end(doc, elements):
    """Move front-matter elements after the section break so they belong to
    the last (content) section, which gets the template header/footer."""
    body = doc.element.body
    sectPr = body.find(qn("w:sectPr"))
    for el in elements:
        body.remove(el)
        sectPr.addprevious(el)


def _page_break_before(doc, el):
    """Insert a page-break paragraph immediately before a given element."""
    p = parse_xml(f'<w:p {nsdecls("w")}/>')
    r = parse_xml(f'<w:r {nsdecls("w")}/>')
    r.append(parse_xml(f'<w:br {nsdecls("w")} w:type="page"/>'))
    p.append(r)
    el.addprevious(p)
    return p


def _ensure_frontmatter(doc, product_name):
    """Make sure revision and TOC blocks exist in the content section.

    When the template provides them, they are used as-is (only the revision
    date is refreshed). Fallbacks with hardcoded content are used only for
    templates that lack the corresponding element.

    The 'Предупреждение' table is intentionally NOT added here: it only
    appears when the MD source actually contains a ``!!! warning`` admonition
    (rendered via ``_render_warning_table`` using the template's table
    structure with the real MD content).
    """
    rev = _find_revision_table(doc)
    if rev is None:
        _heading(doc, "Изменения в документе", 1, numbered=False)
        _revision_fallback(doc)
    else:
        _update_revision_date(rev)

    toc = _find_toc_sdt(doc)
    if toc is None:
        _heading(doc, "Содержание", 1, numbered=False)
        _add_toc_field(doc)
    else:
        _page_break_before(doc, toc)


def _prepare_docx(md_path: Path, product_name: str | None = None, toc_pages: dict | None = None):
    """Build a finished DOCX document from a single markdown file.

    Returns ``(document, content_hdr_rid, content_ftr_rid, toc_entries)`` so
    the caller can either save it to disk or serialize it to bytes. Raises
    ``FileNotFoundError`` when the markdown file does not exist.
    """
    global _MANUAL_HEADING_NUMS
    if not md_path.exists():
        raise FileNotFoundError(f"MD file not found: {md_path}")

    if product_name is None:
        # Derive product name from the file's first H1
        headings = _extract_headings(md_path)
        if headings and headings[0][0] == 1:
            product_name = headings[0][1]
        else:
            product_name = md_path.stem

    fig_cnt = [0]
    tbl_cnt = [0]

    # Pass 1: scan for cross-reference anchors
    _reset_global_counters()
    _MANUAL_HEADING_NUMS = _detect_manual_numbering(md_path)
    scan, _ = _fresh_doc()
    _ensure_heading_styles(scan)
    _init_numbering(scan)
    _render_md(md_path, 1, scan, fig_cnt, tbl_cnt)

    # Pass 2: real document
    _reset_global_counters()
    _MANUAL_HEADING_NUMS = _detect_manual_numbering(md_path)
    doc, front_elems = _fresh_doc()
    _ensure_heading_styles(doc)
    _init_numbering(doc)

    content_hdr_rid, content_ftr_rid = _capture_content_section_refs(doc)

    _title_page(doc, product_name)
    _fit_title_page(doc)
    doc.add_section(WD_SECTION.NEW_PAGE)
    _move_to_body_end(doc, front_elems)
    _ensure_frontmatter(doc, product_name)

    _page_break(doc)

    # Render the MD content starting at heading level 1
    _render_md(md_path, 1, doc, fig_cnt, tbl_cnt)

    doc.core_properties.title = product_name
    doc.core_properties.subject = "Руководство пользователя"

    _add_footer(doc, product_name, content_hdr_rid, content_ftr_rid)
    _set_doc_version(doc, _latest_doc_version())
    _strip_heading_autonum(doc)
    _enable_field_updates(doc)
    toc_entries = _rebuild_toc_entries(doc, toc_pages)

    return doc, content_hdr_rid, content_ftr_rid, toc_entries


def render_docx_with_toc(md_path: Path, product_name: str | None = None,
                         toc_pages: dict | None = None):
    """Generate a DOCX from a single markdown file.

    Returns ``(toc_entries, bytes)`` where ``toc_entries`` is the list of
    ``(level, heading_text)`` written into the TOC field.
    """
    doc, _, _, toc_entries = _prepare_docx(md_path, product_name, toc_pages)
    buffer = io.BytesIO()
    doc.save(buffer)
    return toc_entries, buffer.getvalue()


def render_docx_bytes(md_path: Path, product_name: str | None = None, toc_pages: dict | None = None) -> bytes:
    """Generate a DOCX from a single markdown file and return it as bytes.

    Keeps the document in memory so callers (e.g. the mkdocs PDF hook) can
    convert it without ever writing a DOCX file to disk.
    """
    _, data = render_docx_with_toc(md_path, product_name, toc_pages)
    return data


def generate(md_path: Path, output_dir: Path, product_name: str | None = None):
    """Generate a DOCX from a single markdown file and save it to disk.

    The TOC is built from the heading structure found inside the MD file.
    """
    md_path = md_path.resolve()
    if not md_path.exists():
        print(f"Error: MD file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    doc, _, _, _ = _prepare_docx(md_path, product_name)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    docx_path = output_dir / f"{md_path.stem}.docx"
    doc.save(str(docx_path))
    print(f"DOCX saved: {docx_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Генерация DOCX из одного markdown-файла с оглавлением по его содержанию"
    )
    parser.add_argument("md_file", help="Путь к markdown-файлу")
    parser.add_argument("--output-dir", default=None,
                        help="Каталог для выходного DOCX (по умолчанию — рядом с MD-файлом)")
    parser.add_argument("--product-name", default=None,
                        help="Название продукта для титульной страницы")
    args = parser.parse_args()

    md_path = Path(args.md_file).resolve()
    if not md_path.exists():
        md_path = (DOCS_ROOT / args.md_file).resolve()
    if not md_path.exists():
        print(f"Error: MD file not found: {args.md_file}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else md_path.parent / "output"
    generate(md_path, output_dir, args.product_name)
