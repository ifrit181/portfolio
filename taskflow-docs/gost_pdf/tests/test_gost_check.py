#!/usr/bin/env python3
"""Юнит-тесты gost_pdf/gost_check.py — проверка PDF и отчёт о расхождениях.

Синтетические PDF собираются без LibreOffice (raw PDF + Identity-H +
ToUnicode CMap), поэтому тесты чистые и быстрые.

Запуск (из корня репозитория или taskflow-docs/):

    python -m unittest discover -s taskflow-docs/gost_pdf/tests
    # или
    python -m unittest discover -s gost_pdf/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
GOST_DIR = TESTS_DIR.parent
if str(GOST_DIR) not in sys.path:
    sys.path.insert(0, str(GOST_DIR))

import doc_types  # noqa: E402
import gost_check as gc  # noqa: E402


# -----------------------------------------------------------------------------
# Синтетический PDF: Identity-H + ToUnicode, кириллица извлекается pypdf
# -----------------------------------------------------------------------------

def build_pdf(path: Path, pages: list[list[str]], info: dict | None = None) -> None:
    """Создаёт PDF: страницы = списки строк, info — /Title,/Subject,/Author."""
    chars = sorted({ch for page in pages for line in page for ch in line})
    bfchars = " ".join(f"<{ord(ch):04X}> <{ord(ch):04X}>" for ch in chars)
    cmap = (
        "/CIDInit /ProcSet findresource begin\n12 dict begin\nbegincmap\n"
        "/CMapType 2 def\n"
        "1 begincodespacerange\n<0000> <FFFF>\nendcodespacerange\n"
        f"{len(chars)} beginbfchar\n{bfchars}\nendbfchar\n"
        "endcmap\nCMapName currentdict /CMap defineresource pop\nend\nend\n"
    )

    objs: dict[int, bytes] = {1: b"<< /Type /Catalog /Pages 2 0 R >>"}
    page_ids = []
    next_id = 10
    for page in pages:
        page_id, font_id, stream_id = next_id, next_id + 1, next_id + 2
        next_id += 3
        page_ids.append(page_id)
        content = ""
        y = 800
        for line in page:
            hexs = "".join(f"{ord(ch):04X}" for ch in line)
            content += f"BT /F1 14 Tf 50 {y} Td <{hexs}> Tj ET\n"
            y -= 24
        content_b = content.encode("ascii")
        objs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {stream_id} 0 R >>"
        ).encode()
        objs[font_id] = (
            b"<< /Type /Font /Subtype /Type0 /BaseFont /Helvetica "
            b"/Encoding /Identity-H /DescendantFonts ["
            + f"{next_id} 0 R".encode() + b"] /ToUnicode "
            + f"{next_id + 1} 0 R".encode() + b" >>"
        )
        objs[stream_id] = (
            f"<< /Length {len(content_b)} >>\nstream\n".encode()
            + content_b + b"endstream"
        )
        objs[next_id] = (
            b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /Helvetica "
            b"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) "
            b"/Supplement 0 >> /FontDescriptor "
            + f"{next_id + 2} 0 R".encode() + b" /DW 600 >>"
        )
        objs[next_id + 1] = (
            f"<< /Length {len(cmap.encode('ascii'))} >>\nstream\n".encode()
            + cmap.encode("ascii") + b"endstream"
        )
        objs[next_id + 2] = (
            b"<< /Type /FontDescriptor /FontName /Helvetica /Flags 32 "
            b"/FontBBox [0 0 1000 1000] /ItalicAngle 0 /Ascent 800 "
            b"/Descent -200 /CapHeight 700 /StemV 80 >>"
        )
        next_id += 3

    kids = " ".join(f"{i} 0 R" for i in page_ids)
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

    info_id = None
    if info is not None:
        info_id = 3
        parts = [
            f"/{k} <FEFF{v.encode('utf-16-be').hex().upper()}>"
            for k, v in info.items()
        ]
        objs[3] = ("<< " + " ".join(parts) + " >>").encode()

    out = bytearray(b"%PDF-1.4\n")
    offsets = {}
    for oid in sorted(objs):
        offsets[oid] = len(out)
        out += f"{oid} 0 obj\n".encode() + objs[oid] + b"\nendobj\n"
    xref_pos = len(out)
    max_id = max(objs)
    out += f"xref\n0 {max_id + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for oid in range(1, max_id + 1):
        if oid in offsets:
            out += f"{offsets[oid]:010d} 00000 n \n".encode()
        else:
            out += b"0000000000 65535 f \n"
    trailer = f"trailer\n<< /Size {max_id + 1} /Root 1 0 R"
    if info_id:
        trailer += f" /Info {info_id} 0 R"
    trailer += f" >>\nstartxref\n{xref_pos}\n%%EOF\n"
    out += trailer.encode()
    path.write_bytes(bytes(out))


# -----------------------------------------------------------------------------
# Фикстуры контекста и страниц
# -----------------------------------------------------------------------------

OBOZ = "А.В.00001-01 И3 01-1"
STROKA = "Внесены изменения в раздел"


def ctx_good() -> dict:
    return {
        "doc_type": doc_types.resolve("opisanie-po"),
        "annotation": "Текст аннотации для проверки.",
        "oboznachenie": OBOZ,
        "stroka_izmenenij": STROKA,
        "product_name_used": "СКЛАД-5",
    }


def ctx_bad() -> dict:
    return {
        "doc_type": doc_types.resolve("rukovodstvo-polzovatelya"),
        "annotation": "",
        "oboznachenie": OBOZ,
        "stroka_izmenenij": STROKA,
        "product_name_used": "СКЛАД-5",
    }


GOOD_INFO = {
    "Title": "СКЛАД-5",
    "Subject": "Описание программного обеспечения",
    "Author": "Кудряшова Т.В.",
}


def good_pages() -> list[list[str]]:
    dt = doc_types.resolve("opisanie-po").title
    return [
        ["УТВЕРЖДЕНО", "СКЛАД-5", dt, "Листов 5"],
        ["2", "АННОТАЦИЯ", "Текст аннотации для проверки.", OBOZ, STROKA],
        ["3", "СОДЕРЖАНИЕ", "Введение...........4",
         "Описание операций...4", OBOZ, STROKA],
        ["4", "Введение", "Описание операций", OBOZ, STROKA],
        ["5", "Лист регистрации изменений", OBOZ, STROKA],
    ]


GOOD_ENTRIES = [(2, "Введение"), (2, "Описание операций")]


def run_check(tmp: Path, pages, ctx, entries, info=None,
              name="doc.pdf") -> gc.DocReport:
    pdf = tmp / name
    build_pdf(pdf, pages, info=info)
    rep = gc.DocReport(rel="doc.md")
    rep.doc_type = ctx["doc_type"].title
    rep.standard = ctx["doc_type"].content_standard
    gc.check_pdf(pdf, ctx, entries, rep)
    return rep


def finding(rep: gc.DocReport, group: str):
    """Первый finding по группе (или None)."""
    return next((f for f in rep.findings if f.group == group), None)


def findings(rep: gc.DocReport, group: str):
    return [f for f in rep.findings if f.group == group]


# -----------------------------------------------------------------------------
# _norm / _has_line
# -----------------------------------------------------------------------------

class NormTests(unittest.TestCase):
    def test_casefold_and_whitespace(self):
        self.assertEqual(gc._norm("  СКЛАД\t-5 \n"), "склад -5")

    def test_nbsp_replaced(self):
        self.assertEqual(gc._norm("а\u00a0б"), "а б")

    def test_has_line_exact(self):
        self.assertTrue(gc._has_line("СОДЕРЖАНИЕ\nтекст", "содержание"))

    def test_has_line_rejects_prefix(self):
        # строка содержания с выносками не должна совпадать с заголовком
        self.assertFalse(gc._has_line("СОДЕРЖАНИЕ.....4", "Содержание"))


# -----------------------------------------------------------------------------
# DocReport
# -----------------------------------------------------------------------------

class DocReportTests(unittest.TestCase):
    def test_default_level_ok(self):
        rep = gc.DocReport(rel="a.md")
        self.assertEqual(rep.level, gc.OK)
        self.assertEqual(rep.count(gc.WARN), 0)

    def test_level_escalates_to_warn_then_fail(self):
        rep = gc.DocReport(rel="a.md")
        rep.add(gc.OK, "Г", "x")
        self.assertEqual(rep.level, gc.OK)
        rep.add(gc.WARN, "Г", "y")
        self.assertEqual(rep.level, gc.WARN)
        rep.add(gc.FAIL, "Г", "z")
        self.assertEqual(rep.level, gc.FAIL)
        self.assertEqual(rep.count(gc.OK), 1)
        self.assertEqual(rep.count(gc.WARN), 1)
        self.assertEqual(rep.count(gc.FAIL), 1)

    def test_error_forces_fail(self):
        rep = gc.DocReport(rel="a.md", error="boom")
        self.assertEqual(rep.level, gc.FAIL)


# -----------------------------------------------------------------------------
# check_pdf — положительный сценарий
# -----------------------------------------------------------------------------

class CheckGoodPdfTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_all_checks_pass(self):
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        self.assertEqual(rep.pages, 5)
        self.assertEqual(rep.level, gc.OK,
                         msg="\n".join(
                             f"{f.level} {f.group}: {f.message}"
                             for f in rep.findings))
        self.assertEqual(rep.count(gc.WARN), 0)
        self.assertEqual(rep.count(gc.FAIL), 0)

    def test_title_checks(self):
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        msgs = [f.message for f in findings(rep, "Титул")]
        self.assertEqual(len(msgs), 4)
        self.assertTrue(all("УТВЕРЖДЕНО" in m for m in msgs[:1]))
        self.assertIn("«Листов 5» совпадает с числом страниц", msgs)
        self.assertTrue(any("Описание программного обеспечения" in m
                            for m in msgs))

    def test_structure_checks(self):
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        msgs = [f.message for f in findings(rep, "Структура")]
        self.assertTrue(any("лист 3" in m for m in msgs))
        self.assertTrue(any("все записи содержания найдены (2)" in m
                            for m in msgs))
        self.assertTrue(any("точечные выноски" in m for m in msgs))
        self.assertTrue(any("лист регистрации изменений" in m for m in msgs))

    def test_annotation_and_sections(self):
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        self.assertEqual(finding(rep, "Аннотация").level, gc.OK)
        self.assertEqual(finding(rep, "Разделы").level, gc.OK)
        self.assertIn("не нормируется", finding(rep, "Разделы").message)

    def test_headers_and_numbering(self):
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        msgs = [(f.level, f.message) for f in findings(rep, "Колонтитулы")]
        self.assertEqual(len(msgs), 3)
        self.assertTrue(all(lvl == gc.OK for lvl, _ in msgs), msgs)
        self.assertTrue(any("4 из 4" in m for _, m in msgs))

    def test_single_page_title_without_sheets_line(self):
        pages = [["УТВЕРЖДЕНО", "СКЛАД-5"]]
        rep = run_check(self.tmp, pages, ctx_good(), [])
        sheets = next(f for f in findings(rep, "Титул")
                      if "Листов" in f.message)
        self.assertEqual(sheets.level, gc.OK)
        self.assertIn("не выводится при одном листе", sheets.message)


# -----------------------------------------------------------------------------
# check_pdf — расхождения и ошибки
# -----------------------------------------------------------------------------

class CheckBadPdfTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _bad(self, pages=None, ctx=None, entries=None, info=None):
        if pages is None:
            pages = [
                ["СКЛАД-5", "Vladimir Korychev", "Качество на складах"],
                ["СОДЕРЖАНИЕ", "Введение..........3"],
            ]
        if ctx is None:
            ctx = ctx_bad()
        if entries is None:
            entries = [(2, "Введение"), (2, "Отсутствующий раздел")]
        return run_check(self.tmp, pages, ctx, entries, info=info)

    def test_missing_title_markers_are_fail(self):
        rep = self._bad()
        utverzhdeno = next(f for f in findings(rep, "Титул")
                           if "УТВЕРЖДЕНО" in f.message)
        self.assertEqual(utverzhdeno.level, gc.FAIL)
        sheets = next(f for f in findings(rep, "Титул") if "Листов" in f.message)
        self.assertEqual(sheets.level, gc.FAIL)
        self.assertIn("нет строки", sheets.message)

    def test_forbidden_template_text_is_fail(self):
        rep = self._bad()
        f = finding(rep, "Чужой контент")
        self.assertEqual(f.level, gc.FAIL)
        self.assertIn("Vladimir Korychev", f.message)
        self.assertIn("Качество на складах", f.message)

    def test_missing_structure_is_fail(self):
        rep = self._bad()
        li = next(f for f in findings(rep, "Структура")
                  if "регистрации" in f.message)
        self.assertEqual(li.level, gc.FAIL)

    def test_missing_toc_entries_is_warn(self):
        rep = self._bad()
        toc = next(f for f in findings(rep, "Структура")
                   if "не найдено" in f.message)
        self.assertEqual(toc.level, gc.WARN)
        self.assertIn("1 из 2", toc.message)
        self.assertIn("Отсутствующий раздел", toc.message)

    def test_annotation_required_but_absent_is_warn(self):
        rep = self._bad()
        f = finding(rep, "Аннотация")
        self.assertEqual(f.level, gc.WARN)
        self.assertIn("gost_annotation не задана", f.message)

    def test_annotation_set_but_page_absent_is_fail(self):
        ctx = ctx_good()
        pages = [p for p in good_pages()]
        pages[1] = ["2", "Другая страница", OBOZ, STROKA]
        rep = run_check(self.tmp, pages, ctx, GOOD_ENTRIES, info=GOOD_INFO)
        f = finding(rep, "Аннотация")
        self.assertEqual(f.level, gc.FAIL)
        self.assertIn("не найдена", f.message)

    def test_missing_required_sections_is_warn(self):
        rep = self._bad()
        f = finding(rep, "Разделы")
        self.assertEqual(f.level, gc.WARN)
        self.assertIn("Назначение и условия применения", f.message)
        self.assertIn("ГОСТ Р 59795-2021", f.message)

    def test_all_required_sections_is_ok(self):
        sections = doc_types.resolve("rukovodstvo-polzovatelya").sections
        entries = [(2, s) for s in sections]
        rep = self._bad(entries=entries)
        # разделы в порядке, но прочие проблемы остаются
        self.assertEqual(finding(rep, "Разделы").level, gc.OK)

    def test_absent_header_footer_is_warn(self):
        pages = [
            ["УТВЕРЖДЕНО", "СКЛАД-5", "Листов 2"],
            ["СОДЕРЖАНИЕ", "2"],
        ]
        rep = run_check(self.tmp, pages, ctx_good(), [])
        oboz = finding(rep, "Колонтитулы")
        self.assertEqual(oboz.level, gc.WARN)
        self.assertIn("gost_oboznachenie", oboz.message)

    def test_metadata_empty_is_fail(self):
        rep = self._bad(info=None)
        self.assertEqual(len(findings(rep, "Метаданные")), 3)
        self.assertTrue(all(f.level == gc.FAIL
                            for f in findings(rep, "Метаданные")))

    def test_metadata_mismatch_is_warn(self):
        info = {"Title": "Другое имя", "Subject": "Техническое задание",
                "Author": "Кудряшова Т.В."}
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=info)
        title_f = next(f for f in findings(rep, "Метаданные")
                       if f.message.startswith("/Title"))
        self.assertEqual(title_f.level, gc.WARN)
        subj_f = next(f for f in findings(rep, "Метаданные")
                      if f.message.startswith("/Subject"))
        self.assertEqual(subj_f.level, gc.WARN)

    def test_forbidden_author_is_fail(self):
        info = dict(GOOD_INFO, Author="Vladimir Korychev")
        rep = run_check(self.tmp, good_pages(), ctx_good(), GOOD_ENTRIES,
                        info=info)
        author_f = next(f for f in findings(rep, "Метаданные")
                        if f.message.startswith("/Author"))
        self.assertEqual(author_f.level, gc.FAIL)
        self.assertIn("из шаблона", author_f.message)

    def test_numbering_absent_is_warn(self):
        pages = [list(p) for p in good_pages()]
        # убираем номера страниц (первая строка каждой страницы кроме титула)
        for i in range(1, len(pages)):
            if pages[i][0].isdigit():
                pages[i] = pages[i][1:]
        rep = run_check(self.tmp, pages, ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        num = next(f for f in findings(rep, "Колонтитулы")
                   if "нумерация" in f.message)
        self.assertEqual(num.level, gc.WARN)

    def test_multicolumn_toc_second_page_entries_found(self):
        dt = doc_types.resolve("opisanie-po").title
        pages = [
            ["УТВЕРЖДЕНО", "СКЛАД-5", dt, "Листов 5"],
            ["2", "СОДЕРЖАНИЕ", "Введение...........4"],
            ["3", "Описание операций.....4"],
            ["4", "Введение", "Описание операций"],
            ["5", "Лист регистрации изменений"],
        ]
        rep = run_check(self.tmp, pages, ctx_good(), GOOD_ENTRIES,
                        info=GOOD_INFO)
        toc = next(f for f in findings(rep, "Структура")
                   if "записи содержания" in f.message)
        self.assertEqual(toc.level, gc.OK)
        self.assertIn("(2)", toc.message)
        dots = next(f for f in findings(rep, "Структура")
                    if "точечные" in f.message)
        self.assertIn("(2 лист.)", dots.message)


# -----------------------------------------------------------------------------
# build_report
# -----------------------------------------------------------------------------

class BuildReportTests(unittest.TestCase):
    @staticmethod
    def _ok_report(rel="a.md"):
        rep = gc.DocReport(rel=rel, out=f"assets/pdf-gost/{rel}.pdf",
                           pages=3, doc_type="Вид", standard="ГОСТ X")
        rep.add(gc.OK, "Группа", "всё хорошо")
        return rep

    @staticmethod
    def _warn_report(rel="b.md"):
        rep = gc.DocReport(rel=rel, out=f"assets/pdf-gost/{rel}.pdf",
                           pages=2, doc_type="Вид", standard="ГОСТ X")
        rep.add(gc.OK, "Группа", "ок")
        rep.add(gc.WARN, "Группа", "расхождение")
        return rep

    def test_header_counts(self):
        text = gc.build_report(
            [self._ok_report(), self._warn_report()],
            timestamp="2026-10-09 12:00:00")
        self.assertIn("- Дата сборки: 2026-10-09 12:00:00", text)
        self.assertIn("Документов: **2** — OK: **1**, "
                      "с предупреждениями: **1**, с ошибками: **0**", text)
        self.assertIn("Проверок: **3** — предупреждений: **1**, ошибок: **0**",
                      text)
        self.assertIn("- Фильтр: все файлы", text)

    def test_only_filter_shown(self):
        text = gc.build_report([], timestamp="t", only="index.md,faq.md")
        self.assertIn("- Фильтр: `index.md,faq.md`", text)

    def test_summary_table_rows(self):
        text = gc.build_report(
            [self._ok_report(), self._warn_report()], timestamp="t")
        self.assertIn("| 1 | a.md | `assets/pdf-gost/a.md.pdf` | 3 | 1 | 0 "
                      "| 0 | **OK** |", text)
        self.assertIn("| 2 | b.md | `assets/pdf-gost/b.md.pdf` | 2 | 1 | 1 "
                      "| 0 | **WARN** |", text)

    def test_divergences_section_lists_warns(self):
        text = gc.build_report([self._warn_report()], timestamp="t")
        section = text.split("## Расхождения")[1].split("## Проверки")[0]
        self.assertIn("- **WARN** · b.md — Группа: расхождение", section)
        self.assertNotIn("всё хорошо", section)

    def test_clean_reports_say_no_divergences(self):
        text = gc.build_report([self._ok_report()], timestamp="t")
        section = text.split("## Расхождения")[1].split("## Проверки")[0]
        self.assertIn("Расхождений не обнаружено.", section)

    def test_error_report_in_divergences_and_summary(self):
        rep = gc.DocReport(rel="bad.md", error="RuntimeError: boom")
        text = gc.build_report([rep], timestamp="t")
        self.assertIn("| 1 | bad.md | — | — | — | — | 1 | **FAIL** |", text)
        self.assertIn("- **FAIL** · bad.md — сборка не выполнена: "
                      "RuntimeError: boom", text)

    def test_details_section_lists_all_findings(self):
        text = gc.build_report([self._warn_report()], timestamp="t")
        details = text.split("## Проверки по файлам")[1]
        self.assertIn("### 1. b.md", details)
        self.assertIn("- **OK** · Группа · ок", details)
        self.assertIn("- **WARN** · Группа · расхождение", details)
        self.assertIn("- Итог: **WARN**", details)

    def test_error_report_details_show_error_only(self):
        rep = gc.DocReport(rel="bad.md", error="нет файла")
        text = gc.build_report([rep], timestamp="t")
        details = text.split("## Проверки по файлам")[1]
        self.assertIn("- **FAIL** · Сборка: нет файла", details)

    def test_empty_reports(self):
        text = gc.build_report([], timestamp="t")
        self.assertIn("Документов: **0**", text)
        self.assertIn("Расхождений не обнаружено.", text)


if __name__ == "__main__":
    unittest.main()
