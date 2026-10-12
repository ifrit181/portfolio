#!/usr/bin/env python3
"""Юнит- и интеграционные тесты gost_pdf/generate_pdf_gost.py.

Юнит-тесты не требуют LibreOffice; интеграционный
(`GeneratePdfIntegrationTests`) собирает один документ end-to-end
(нужен `soffice` в PATH) — он помечен skipUnless.

Запуск (из корня репозитория или taskflow-docs/):

    python -m unittest discover -s taskflow-docs/gost_pdf/tests
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
GOST_DIR = TESTS_DIR.parent
if str(GOST_DIR) not in sys.path:
    sys.path.insert(0, str(GOST_DIR))

import generate_pdf_gost as gen  # noqa: E402
import gost_check  # noqa: E402


# -----------------------------------------------------------------------------
# _split_front_matter
# -----------------------------------------------------------------------------

class SplitFrontMatterTests(unittest.TestCase):
    def test_plain_front_matter(self):
        meta, body = gen._split_front_matter("---\na: 1\n---\nТекст")
        self.assertEqual(meta, {"a": 1})
        self.assertEqual(body, "Текст")

    def test_bom_stripped(self):
        meta, body = gen._split_front_matter("\ufeff---\nx: y\n---\nТело")
        self.assertEqual(meta, {"x": "y"})
        self.assertEqual(body, "Тело")

    def test_no_front_matter(self):
        meta, body = gen._split_front_matter("# Заголовок\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Заголовок\n")

    def test_invalid_yaml_returns_empty_meta(self):
        meta, body = gen._split_front_matter("---\na: [1\n---\nТекст")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Текст")

    def test_non_dict_yaml_returns_empty_meta(self):
        meta, body = gen._split_front_matter("---\n- 1\n- 2\n---\nТекст")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Текст")

    def test_empty_front_matter(self):
        meta, body = gen._split_front_matter("---\n---\nТекст")
        self.assertEqual(meta, {})
        self.assertEqual(body, "Текст")


# -----------------------------------------------------------------------------
# _flag / _s
# -----------------------------------------------------------------------------

class FlagTests(unittest.TestCase):
    def test_bool_passthrough(self):
        self.assertTrue(gen._flag(True))
        self.assertFalse(gen._flag(False))

    def test_none_is_false(self):
        self.assertFalse(gen._flag(None))

    def test_truthy_strings(self):
        for v in ("1", "true", "True", "YES", "on", "да", "ДА"):
            self.assertTrue(gen._flag(v), v)

    def test_falsy_strings(self):
        for v in ("0", "false", "no", "off", "нет", "", "  ", "может"):
            self.assertFalse(gen._flag(v), v)


class SValueTests(unittest.TestCase):
    def test_none_empty(self):
        self.assertEqual(gen._s(None), "")

    def test_strips(self):
        self.assertEqual(gen._s("  значение  "), "значение")

    def test_number_stringified(self):
        self.assertEqual(gen._s(42), "42")


# -----------------------------------------------------------------------------
# _collect_ctx
# -----------------------------------------------------------------------------

class CollectCtxTests(unittest.TestCase):
    def test_defaults(self):
        ctx = gen._collect_ctx({}, None)
        self.assertEqual(ctx["doc_type"].key, "rukovodstvo-polzovatelya")
        self.assertEqual(ctx["oboznachenie"], "")
        self.assertFalse(ctx["left30"])
        self.assertEqual(ctx["annotation"], "")
        self.assertEqual(ctx["author"], "")
        self.assertIsNone(ctx["product_name"])

    def test_doc_type_from_meta_key(self):
        ctx = gen._collect_ctx({"gost_doc_type": "tz"}, None)
        self.assertEqual(ctx["doc_type"].key, "tz")

    def test_doc_type_russian_alias(self):
        ctx = gen._collect_ctx({"gost_doc_type": "Техническое задание"}, None)
        self.assertEqual(ctx["doc_type"].key, "tz")

    def test_override_beats_meta(self):
        ctx = gen._collect_ctx({"gost_doc_type": "tz"}, "spetsifikatsiya")
        self.assertEqual(ctx["doc_type"].key, "spetsifikatsiya")

    def test_left30_parsed(self):
        ctx = gen._collect_ctx({"gost_left_margin_30": "да"}, None)
        self.assertTrue(ctx["left30"])

    def test_all_string_fields(self):
        meta = {
            "gost_product_name": " Система ",
            "gost_oboznachenie": "ТС 1",
            "gost_litera": "Э",
            "gost_otmetka_ucheta": "Экз. № 1",
            "gost_stroka_izmenenij": "Версия 1.2",
            "gost_lu_oboznachenie": "ТС 1-ЛУ",
            "gost_ministerstvo": "Минцифры",
            "gost_author": "Иванов И.И.",
        }
        ctx = gen._collect_ctx(meta, None)
        self.assertEqual(ctx["product_name"], "Система")
        self.assertEqual(ctx["oboznachenie"], "ТС 1")
        self.assertEqual(ctx["litera"], "Э")
        self.assertEqual(ctx["otmetka_ucheta"], "Экз. № 1")
        self.assertEqual(ctx["stroka_izmenenij"], "Версия 1.2")
        self.assertEqual(ctx["lu_oboznachenie"], "ТС 1-ЛУ")
        self.assertEqual(ctx["ministerstvo"], "Минцифры")
        self.assertEqual(ctx["author"], "Иванов И.И.")

    def test_annotation_multiline(self):
        ctx = gen._collect_ctx({"gost_annotation": "блок 1\n\nблок 2"}, None)
        self.assertEqual(ctx["annotation"], "блок 1\n\nблок 2")


# -----------------------------------------------------------------------------
# _norm_rel / _walk_docs / _iter_nav_files
# -----------------------------------------------------------------------------

class NormRelTests(unittest.TestCase):
    def test_backslashes(self):
        self.assertEqual(gen._norm_rel("a\\b\\c.md"), "a/b/c.md")

    def test_leading_slash(self):
        self.assertEqual(gen._norm_rel("/index.md"), "index.md")

    def test_whitespace(self):
        self.assertEqual(gen._norm_rel("  a.md  "), "a.md")


class WalkDocsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self._tmp.name) / "docs"

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, rel: str):
        p = self.docs / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# x\n", encoding="utf-8")

    def test_walk_sorted_and_filtered(self):
        for rel in ("b.md", "a.md", "sub/c.md", "snippets/s.md",
                    ".hidden.md", "snippets/deep/t.md"):
            self._write(rel)
        got = list(gen._walk_docs(self.docs))
        self.assertEqual(got, ["a.md", "b.md", "sub/c.md"])


class IterNavFilesTests(unittest.TestCase):
    def test_none_yields_nothing(self):
        self.assertEqual(list(gen._iter_nav_files(None)), [])

    def test_flat_list(self):
        nav = ["index.md", "faq.md"]
        self.assertEqual(list(gen._iter_nav_files(nav)), ["index.md", "faq.md"])

    def test_dict_entries(self):
        nav = [{"Home": "index.md"}, {"Guide": "guide/index.md"}]
        self.assertEqual(list(gen._iter_nav_files(nav)),
                         ["index.md", "guide/index.md"])

    def test_nested(self):
        nav = [{"Руководство": ["user.md", {"Продвинутый": "adv.md"}]}]
        self.assertEqual(list(gen._iter_nav_files(nav)),
                         ["user.md", "adv.md"])

    def test_title_path_pair_nested(self):
        # пара [заголовок, путь] как элемент nav-списка: берётся путь
        nav = [["Главная", "index.md"]]
        self.assertEqual(list(gen._iter_nav_files(nav)), ["index.md"])


# -----------------------------------------------------------------------------
# _write_report
# -----------------------------------------------------------------------------

class WriteReportTests(unittest.TestCase):
    @staticmethod
    def _reports():
        rep = gost_check.DocReport(rel="a.md", out="assets/pdf-gost/a.pdf",
                                   pages=3, doc_type="Вид")
        rep.add(gost_check.OK, "Группа", "ок")
        return [rep]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.site = Path(self._tmp.name) / "site"

    def tearDown(self):
        self._tmp.cleanup()

    def test_default_path_under_site(self):
        gen._write_report(self._reports(), self.site, None,
                          only=None, report_path=None)
        out = self.site / "assets" / "pdf-gost" / "check-report.md"
        self.assertTrue(out.exists())
        text = out.read_text(encoding="utf-8")
        self.assertIn("a.md", text)
        self.assertIn("# Отчёт проверки PDF по ГОСТ", text)

    def test_report_off_writes_nothing(self):
        gen._write_report(self._reports(), self.site, None,
                          only=None, report_path="off")
        self.assertFalse((self.site / "assets" / "pdf-gost"
                          / "check-report.md").exists())
        self.assertFalse(self.site.exists())

    def test_absolute_path(self):
        target = Path(self._tmp.name) / "custom.md"
        gen._write_report(self._reports(), self.site, None,
                          only=None, report_path=str(target))
        self.assertTrue(target.exists())

    def test_relative_path_under_site(self):
        gen._write_report(self._reports(), self.site, None,
                          only=None, report_path="reports/check.md")
        self.assertTrue((self.site / "reports" / "check.md").exists())

    def test_only_list_joined(self):
        gen._write_report(self._reports(), self.site, None,
                          only=["index.md", "faq.md"], report_path=None)
        text = (self.site / "assets" / "pdf-gost" / "check-report.md") \
            .read_text(encoding="utf-8")
        self.assertIn("- Фильтр: `index.md,faq.md`", text)

    def test_explicit_timestamp_shown(self):
        gen._write_report(self._reports(), self.site,
                          gen.datetime.datetime(2026, 10, 9, 12, 0, 0),
                          only=None, report_path=None)
        text = (self.site / "assets" / "pdf-gost" / "check-report.md") \
            .read_text(encoding="utf-8")
        self.assertIn("2026-10-09 12:00:00", text)

    def test_none_timestamp_uses_current_time(self):
        gen._write_report(self._reports(), self.site, None,
                          only=None, report_path=None)
        text = (self.site / "assets" / "pdf-gost" / "check-report.md") \
            .read_text(encoding="utf-8")
        self.assertRegex(text, r"- Дата сборки: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")


# -----------------------------------------------------------------------------
# on_post_build — отключение DOCX2PDF=off
# -----------------------------------------------------------------------------

class DisabledBuildTests(unittest.TestCase):
    def test_off_env_skips_everything(self):
        self._tmp = tempfile.TemporaryDirectory()
        try:
            site = Path(self._tmp.name) / "site"
            docs = Path(self._tmp.name) / "docs"
            docs.mkdir()
            (docs / "a.md").write_text("# A\n", encoding="utf-8")
            old = os.environ.get("DOCX2PDF")
            os.environ["DOCX2PDF"] = "off"
            try:
                gen.on_post_build({"docs_dir": str(docs),
                                   "site_dir": str(site)})
            finally:
                if old is None:
                    os.environ.pop("DOCX2PDF", None)
                else:
                    os.environ["DOCX2PDF"] = old
            self.assertFalse((site / "assets" / "pdf-gost"
                              / "check-report.md").exists())
        finally:
            self._tmp.cleanup()


# -----------------------------------------------------------------------------
# Интеграция: полный цикл с LibreOffice
# -----------------------------------------------------------------------------

SAMPLE_MD = """---
gost_doc_type: rukovodstvo-polzovatelya
gost_oboznachenie: "А.В.00001-01 И3 01-1"
gost_litera: "Э"
gost_stroka_izmenenij: "Внесены изменения в раздел"
gost_annotation: |
  Аннотация тестового документа для интеграционного теста.
---

# Тестовая система

## Введение

Тестовый документ проверяет полный цикл сборки.

## Назначение и условия применения

Раздел обязателен для руководства пользователя.

## Подготовка к работе

- пункт списка;

## Описание операций

1. Первое действие.
2. Второе действие.

## Аварийные ситуации

Нажать кнопку сброса.

## Рекомендации по освоению

Читать по порядку.
"""


@unittest.skipUnless(shutil.which("soffice"), "soffice не найден в PATH")
class GeneratePdfIntegrationTests(unittest.TestCase):
    """Полный цикл: MD → DOCX → PDF ×2 → проверка → check-report.md.

    docs_dir создаётся внутри taskflow-docs: generate_single вычисляет
    относительные пути от DOCS_ROOT и падает на чужих корневых каталогах.
    """

    def setUp(self):
        # ВАЖНО: каталог внутри taskflow-docs (см. докстринг)
        self.docs = gen.PROJECT_ROOT / ".gost-pdf-selftest" / "docs"
        shutil.rmtree(self.docs.parent, ignore_errors=True)
        self.docs.mkdir(parents=True)
        (self.docs / "sample.md").write_text(SAMPLE_MD, encoding="utf-8")
        self._tmp = tempfile.TemporaryDirectory()
        self.site = Path(self._tmp.name) / "site"
        self._old_env = os.environ.pop("DOCX2PDF", None)

    def tearDown(self):
        shutil.rmtree(self.docs.parent, ignore_errors=True)
        self._tmp.cleanup()
        if self._old_env is not None:
            os.environ["DOCX2PDF"] = self._old_env

    def test_full_cycle_produces_pdf_and_ok_report(self):
        gen.on_post_build({"docs_dir": str(self.docs),
                           "site_dir": str(self.site)})

        pdf = self.site / "assets" / "pdf-gost" / "sample.pdf"
        self.assertTrue(pdf.exists(), "PDF не создан")

        from pypdf import PdfReader
        reader = PdfReader(str(pdf))
        self.assertGreaterEqual(len(reader.pages), 5)
        self.assertEqual(reader.metadata.title, "Тестовая система")
        self.assertEqual(reader.metadata.subject,
                         "Руководство пользователя")
        self.assertNotEqual(reader.metadata.author, "Vladimir Korychev")

        report = (self.site / "assets" / "pdf-gost" / "check-report.md")
        self.assertTrue(report.exists(), "отчёт не создан")
        text = report.read_text(encoding="utf-8")
        self.assertIn("1 | sample.md", text)
        self.assertIn("| **OK** |", text)
        self.assertIn("Расхождений не обнаружено.", text)
        # ключевые проверки прошли
        self.assertIn("все записи содержания найдены", text)
        self.assertIn("лист регистрации изменений присутствует", text)
        self.assertIn("страница «АННОТАЦИЯ» присутствует", text)


if __name__ == "__main__":
    unittest.main()
