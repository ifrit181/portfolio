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
    2. Раздел «Изменения в документе» (таблица версий + предупреждение)
    3. Раздел «Содержание» (автообновляемое Word-поле TOC по заголовкам MD)
    4. Основное содержимое MD-файла с нумерацией разделов
    5. Колонтитуры (название в шапке, копирайт в подвале)
"""

import argparse
import copy
import datetime
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
    r.font.name = "Arial"
    if size:
        r.font.size = size
    if color:
        r.font.color.rgb = color
    return r


def _hyperlink_run(par, text, bookmark):
    run = par.add_run(text)
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


def _hsize(run, level):
    sizes = {1: 18, 2: 16, 3: 14, 4: 13, 5: 12, 6: 11}
    run.font.size = Pt(sizes.get(level, 12))
    run.font.color.rgb = RGBColor(0x80, 0xBC, 0x48)
    run.font.name = "Arial"


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
    for r in h.runs:
        _hsize(r, level)
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


def _add_footer(doc, year: int, product_name: str):
    for idx, section in enumerate(doc.sections):
        if idx == 0:
            rId = _find_rel_id(doc, "footer1.xml")
            if rId:
                _set_footer_ref(section, rId, "default")
            for ref in list(section._sectPr.findall(qn("w:headerReference"))):
                section._sectPr.remove(ref)
            continue

        footer = section.footer
        footer.is_linked_to_previous = False
        for p in list(footer.paragraphs):
            p._element.getparent().remove(p._element)
        for t in list(footer.tables):
            t._element.getparent().remove(t._element)
        p = footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_run(p, f"©Группа компаний «Цифра», {year}. Все права защищены.",
                 size=Pt(9), color=RGBColor(0x66, 0x66, 0x66))

        header_rId = _find_rel_id(doc, "header1.xml")
        if header_rId:
            _set_header_ref(section, header_rId, "default")
        header = section.header
        header.is_linked_to_previous = False
        _update_header_text(header, product_name)


# --- admonition styles ---

_ADMON_STYLE = {
    "note": {"fill": "E3F2FD", "border": "1E88E5", "title": "Примечание", "title_color": "1565C0"},
    "info": {"fill": "E0F7FA", "border": "00ACC1", "title": "Сведения", "title_color": "00838F"},
    "tip": {"fill": "E8F5E9", "border": "43A047", "title": "Совет", "title_color": "2E7D32"},
    "warning": {"fill": "FFF8E1", "border": "FFA000", "title": "Важно", "title_color": "E65100"},
    "danger": {"fill": "FFEBEE", "border": "E53935", "title": "Опасно", "title_color": "C62828"},
    "question": {"fill": "F3E5F5", "border": "8E24AA", "title": "Вопрос", "title_color": "6A1B9A"},
}


def _rgb(hexstr: str) -> RGBColor:
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16))


def _add_admonition(doc, kind: str, title: str):
    st = _ADMON_STYLE.get(kind, _ADMON_STYLE["note"])
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = t.cell(0, 0)
    cell.width = Inches(6.3)
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(
        f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{st["fill"]}"/>'
    ))
    tcPr.append(parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="12" w:space="0" w:color="{st["border"]}"/>'
        f'<w:left w:val="single" w:sz="12" w:space="0" w:color="{st["border"]}"/>'
        f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="{st["border"]}"/>'
        f'<w:right w:val="single" w:sz="12" w:space="0" w:color="{st["border"]}"/>'
        f'</w:tcBorders>'
    ))
    tcPr.append(parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="120" w:type="dxa"/><w:left w:w="160" w:type="dxa"/>'
        f'<w:bottom w:w="120" w:type="dxa"/><w:right w:w="160" w:type="dxa"/>'
        f'</w:tcMar>'
    ))
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_run(p, title, bold=True, size=Pt(11), color=_rgb(st["title_color"]))
    p.paragraph_format.space_after = Pt(4)
    return t, cell


# --- render markdown ---

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
                pc = doc.add_paragraph()
                pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _add_run(pc, f"Рисунок {fig_cnt[0]} - {ct or alt}", italic=True, size=Pt(10))
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
            title = qt.group(1).strip() if qt else (resto or _ADMON_STYLE.get(kind, _ADMON_STYLE["note"])["title"])
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
                t, cell = _add_admonition(doc, kind, title)
                for cl in clines:
                    ct = cl.strip()
                    if not ct:
                        cell.add_paragraph()
                        continue
                    p = cell.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    p.paragraph_format.space_after = Pt(2)
                    _inline(p, ct, md_rel, fig_cnt)
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
                    pc = doc.add_paragraph()
                    pc.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    _add_run(pc, f"Таблица {tbl_cnt[0]} - {cap_text}", bold=True, size=Pt(10))
            if rows:
                nc = max(len(r) for r in rows)
                t = doc.add_table(rows=len(rows), cols=nc)
                t.style = "Table Grid"
                t.alignment = WD_TABLE_ALIGNMENT.CENTER
                for ri, rc in enumerate(rows):
                    for ci in range(nc):
                        cell = t.cell(ri, ci)
                        cell.text = ""
                        _inline(cell.paragraphs[0], rc[ci] if ci < len(rc) else "")
                        if ri == 0:
                            sh = parse_xml(f'<w:shd {nsdecls("w")} w:fill="E8F5E9"/>')
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
    text = md_path.read_text(encoding="utf-8")
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
    for line in md_path.read_text(encoding="utf-8").split("\n"):
        hm = re.match(r'^(#{2,6})\s+(.*)', line)
        if not hm:
            continue
        title = _clean(hm.group(2))
        if _MANUAL_NUM_RE.match(title):
            return True
    return False


# --- title page / revision / warning ---

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
        for row_idx in (2, 3):
            if row_idx >= len(t.rows):
                continue
            for p in t.rows[row_idx].cells[0].paragraphs:
                if p.text.strip():
                    p.clear()
                    _add_run(p, product_name, size=Pt(32),
                             color=RGBColor(0x80, 0xBC, 0x48))
                    return


def _revision(doc):
    t = doc.add_table(rows=2, cols=4)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ci, h in enumerate(["Версия", "Дата", "Автор", "Описание"]):
        c = t.cell(0, ci)
        c.text = ""
        _add_run(c.paragraphs[0], h, bold=True)
        c._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="E8F5E9"/>'))
    today = datetime.date.today().strftime("%Y-%m-%d")
    for ci, d in enumerate(["1.0", today, "Система", "Начальная версия документа"]):
        t.cell(1, ci).text = ""
        t.cell(1, ci).paragraphs[0].add_run(d)


def _warning(doc):
    t = doc.add_table(rows=2, cols=1)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    c0 = t.cell(0, 0)
    c0.text = ""
    _add_run(c0.paragraphs[0], "Предупреждение", bold=True, size=Pt(12),
             color=RGBColor(0xCC, 0, 0))
    c0._tc.get_or_add_tcPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="FFEBEE"/>'))
    c1 = t.cell(1, 0)
    c1.text = ""
    _add_run(c1.paragraphs[0],
             "Данный документ является интеллектуальной собственностью. "
             "Все права защищены. Копирование и распространение без разрешения запрещено.",
             size=Pt(10))


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


def _fresh_doc() -> Document:
    doc = Document(str(PRIMER_DOCX))
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    tables = list(doc.tables)
    for t in reversed(tables[1:]):
        t._element.getparent().remove(t._element)
    for s in list(doc.element.body.findall(qn("w:sdt"))):
        if s.getparent() is not None and s.getparent().tag != qn("w:tc"):
            doc.element.body.remove(s)
    return doc


def _build_toc_from_headings(doc, headings: list[tuple[int, str]]):
    """Insert a manual table of contents based on the extracted headings.

    Uses Word TOC field so it auto-updates when opened in Word.
    The headings from the MD are rendered with their numbers, and the TOC
    field picks them up via outline levels.
    """
    _add_toc_field(doc)


def generate(md_path: Path, output_dir: Path, product_name: str | None = None):
    """Generate a DOCX from a single markdown file.

    The TOC is built from the heading structure found inside the MD file.
    """
    global _MANUAL_HEADING_NUMS
    if not md_path.exists():
        print(f"Error: MD file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

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
    scan = _fresh_doc()
    _ensure_heading_styles(scan)
    _init_numbering(scan)
    _render_md(md_path, 1, scan, fig_cnt, tbl_cnt)

    # Pass 2: real document
    _reset_global_counters()
    _MANUAL_HEADING_NUMS = _detect_manual_numbering(md_path)
    doc = _fresh_doc()
    _ensure_heading_styles(doc)
    _init_numbering(doc)

    _title_page(doc, product_name)
    doc.add_section(WD_SECTION.NEW_PAGE)

    _heading(doc, "Изменения в документе", 1, numbered=False)
    _revision(doc)
    _warning(doc)

    _page_break(doc)

    _heading(doc, "Содержание", 1, numbered=False)
    _add_toc_field(doc)

    _page_break(doc)

    # Render the MD content starting at heading level 1
    _render_md(md_path, 1, doc, fig_cnt, tbl_cnt)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = md_path.stem
    docx_path = output_dir / f"{stem}.docx"

    doc.core_properties.title = product_name
    doc.core_properties.subject = "Руководство пользователя"

    _add_footer(doc, datetime.date.today().year, product_name)
    _strip_heading_autonum(doc)
    _enable_field_updates(doc)

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
