#!/usr/bin/env python3
"""Юнит-тесты для process_includes.py.

Запуск (из корня репозитория или zensical/):

    python3 -m unittest discover -s zensical/tests
    # или
    python3 -m unittest zensical.tests.test_process_includes

Зависимости только из стандартной библиотеки (unittest, tempfile),
плюс PyYAML, который уже требуется самому скрипту.
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
ZENSICAL_DIR = TESTS_DIR.parent
if str(ZENSICAL_DIR) not in sys.path:
    sys.path.insert(0, str(ZENSICAL_DIR))

import process_includes as pi  # noqa: E402


# -----------------------------------------------------------------------------
# Вспомогательное: временное дерево данных
# -----------------------------------------------------------------------------

def make_docs(tmp: Path, files: dict[str, str | bytes]) -> Path:
    """Создаёт docs_dir из словаря «относительный путь -> содержимое»."""
    docs_dir = tmp / "docs"
    for rel, content in files.items():
        path = docs_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return docs_dir


# -----------------------------------------------------------------------------
# _is_relative_path
# -----------------------------------------------------------------------------

class IsRelativePathTests(unittest.TestCase):
    def test_relative_single_dot(self):
        self.assertTrue(pi._is_relative_path("./snippet.md"))

    def test_relative_double_dot(self):
        self.assertTrue(pi._is_relative_path("../snippet.md"))

    def test_relative_nested(self):
        self.assertTrue(pi._is_relative_path("../../general_snippets/s.md"))

    def test_plain_path_is_not_relative(self):
        self.assertFalse(pi._is_relative_path("general_snippets/s.md"))

    def test_absolute_like_is_not_relative(self):
        self.assertFalse(pi._is_relative_path("/root/snippet.md"))


# -----------------------------------------------------------------------------
# _resolve_include_path
# -----------------------------------------------------------------------------

class ResolveIncludePathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.docs_dir = self.root / "docs"
        self.docs_dir.mkdir()
        self.includer = self.docs_dir / "sub" / "page.md"
        self.includer.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_relative_path_resolves_from_includer(self):
        got = pi._resolve_include_path(
            "../snippets/s.md", self.includer, self.docs_dir
        )
        expected = (self.docs_dir / "snippets" / "s.md").resolve()
        self.assertEqual(got, expected)

    def test_non_relative_path_resolves_from_docs_dir(self):
        got = pi._resolve_include_path(
            "snippets/s.md", self.includer, self.docs_dir
        )
        expected = (self.docs_dir / "snippets" / "s.md").resolve()
        self.assertEqual(got, expected)


# -----------------------------------------------------------------------------
# _filter_inclusion
# -----------------------------------------------------------------------------

class FilterInclusionTests(unittest.TestCase):
    TEXT = (
        "шапка\n"
        "<!--s-->\n"
        "внутри 1\n"
        "<!--e-->\n"
        "хвост\n"
        "<!--s-->\n"
        "внутри 2\n"
        "<!--e-->\n"
        "конец\n"
    )

    def test_no_markers_returns_full_text(self):
        self.assertEqual(pi._filter_inclusion(self.TEXT, None, None), self.TEXT)

    def test_start_only_includes_tail_after_marker(self):
        got = pi._filter_inclusion(self.TEXT, "<!--s-->", None)
        self.assertTrue(got.startswith("\nвнутри 1"))
        self.assertIn("хвост", got)
        self.assertFalse(got.startswith("шапка"))

    def test_end_only_includes_head_before_marker(self):
        got = pi._filter_inclusion(self.TEXT, None, "<!--e-->")
        self.assertNotIn("<!--e-->", got)
        self.assertIn("шапка", got)
        self.assertIn("внутри 1", got)
        self.assertNotIn("хвост", got)
        self.assertNotIn("внутри 2", got)

    def test_both_markers_includes_all_segments(self):
        got = pi._filter_inclusion(self.TEXT, "<!--s-->", "<!--e-->")
        self.assertEqual(got, "\nвнутри 1\n\nвнутри 2\n")
        self.assertNotIn("<!--s-->", got)
        self.assertNotIn("<!--e-->", got)

    def test_start_not_found_with_start_only_returns_empty(self):
        self.assertEqual(
            pi._filter_inclusion(self.TEXT, "<!--missing-->", None), ""
        )

    def test_end_not_found_with_end_only_returns_full_text(self):
        self.assertEqual(
            pi._filter_inclusion(self.TEXT, None, "<!--missing-->"), self.TEXT
        )

    def test_start_not_found_with_both_returns_segments_between_ends(self):
        got = pi._filter_inclusion(self.TEXT, "<!--missing-->", "<!--e-->")
        self.assertEqual(got, "шапка\n<!--s-->\nвнутри 1\n\nконец\n")

    def test_end_not_found_with_both_returns_after_start(self):
        got = pi._filter_inclusion(self.TEXT, "<!--s-->", "<!--missing-->")
        self.assertIn("внутри 1", got)
        self.assertIn("хвост", got)


# -----------------------------------------------------------------------------
# _rewrite_relative_urls
# -----------------------------------------------------------------------------

class RewriteRelativeUrlsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / "docs" / "snippets" / "s.md"
        self.dst = self.root / "docs" / "pages" / "index.md"
        self.src.parent.mkdir(parents=True)
        self.dst.parent.mkdir(parents=True)
        self.rewrite = lambda text: pi._rewrite_relative_urls(
            text, self.src, self.dst
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_md_link_rewritten(self):
        md = "[сниппет](../assets/s.md)"
        got = self.rewrite(md)
        self.assertEqual(got, "[сниппет](../assets/s.md)")

    def test_image_md_link_rewritten(self):
        md = "![картинка](../assets/pic.png)"
        got = self.rewrite(md)
        self.assertEqual(got, "![картинка](../assets/pic.png)")

    def test_html_img_rewritten(self):
        md = '<img src="../assets/pic.png" alt="x">'
        got = self.rewrite(md)
        self.assertEqual(got, '<img src="../assets/pic.png" alt="x">')

    def test_html_anchor_rewritten(self):
        md = '<a href="../page.md">ссылка</a>'
        got = self.rewrite(md)
        self.assertEqual(got, '<a href="../page.md">ссылка</a>')

    def test_trailing_slash_preserved(self):
        md = "[раздел](../folder/)"
        got = self.rewrite(md)
        self.assertEqual(got, "[раздел](../folder/)")

    def test_relative_to_snippet_dir_becomes_visible_from_depth(self):
        md = "![локально](./img.png)"
        got = self.rewrite(md)
        self.assertEqual(got, "![локально](../snippets/img.png)")

    def test_absolute_url_unchanged(self):
        for url in (
            "https://example.com/a.png",
            "ftp://x/y.pdf",
            "mailto:a@b.c",
            "tel:+71234567890",
            "data:image/png;base64,xx",
        ):
            md = f"![x]({url})"
            self.assertEqual(self.rewrite(md), md)

    def test_docs_root_path_unchanged(self):
        md = "[x](/root/page.md)"
        self.assertEqual(self.rewrite(md), md)

    def test_anchor_unchanged(self):
        md = "[раздел](#section)"
        self.assertEqual(self.rewrite(md), md)


# -----------------------------------------------------------------------------
# _preprocess_markdown
# -----------------------------------------------------------------------------

class PreprocessMarkdownTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.docs_dir = self.root / "docs"
        self.docs_dir.mkdir()
        self.current = self.docs_dir / "page.md"

    def tearDown(self):
        self.tmp.cleanup()

    def preprocess(self, content, current=None, seen=None, rewrite=True):
        return pi._preprocess_markdown(
            content,
            current or self.current,
            self.docs_dir,
            seen or set(),
            rewrite,
        )

    def test_full_include_replaced(self):
        snippet = self.docs_dir / "snippets" / "hello.md"
        snippet.parent.mkdir()
        snippet.write_text("Привет, мир!", encoding="utf-8")
        content = (
            "Заголовок\n\n"
            '{%\n    include-markdown "snippets/hello.md"\n%}\n'
            "Конец\n"
        )
        got = self.preprocess(content)
        self.assertIn("Привет, мир!", got)
        self.assertNotIn("include-markdown", got)
        self.assertNotIn("%}", got)

    def test_start_end_filtered(self):
        snippet = self.docs_dir / "snippets" / "s.md"
        snippet.parent.mkdir()
        snippet.write_text(
            "шапка\n<!--s-->\nсередина\n<!--e-->\nхвост\n",
            encoding="utf-8",
        )
        content = (
            '{%\n    include-markdown "snippets/s.md"\n'
            '    start="<!--s-->"\n    end="<!--e-->"\n%}\n'
        )
        got = self.preprocess(content)
        self.assertIn("середина", got)
        self.assertNotIn("шапка", got)
        self.assertNotIn("хвост", got)
        self.assertNotIn("<!--s-->", got)
        self.assertNotIn("<!--e-->", got)

    def test_nested_includes_expanded(self):
        outer = self.docs_dir / "snippets" / "outer.md"
        inner = self.docs_dir / "snippets" / "inner.md"
        outer.parent.mkdir(parents=True, exist_ok=True)
        inner.parent.mkdir(parents=True, exist_ok=True)
        outer.write_text(
            'A {% include-markdown "snippets/inner.md" %} B', encoding="utf-8"
        )
        inner.write_text("INNER", encoding="utf-8")
        content = '{% include-markdown "snippets/outer.md" %}'
        got = self.preprocess(content)
        self.assertIn("INNER", got)
        self.assertNotIn("include-markdown", got)

    def test_cycle_protected(self):
        a = self.docs_dir / "a.md"
        b = self.docs_dir / "b.md"
        a.write_text('A {% include-markdown "b.md" %} A', encoding="utf-8")
        b.write_text('B {% include-markdown "a.md" %} B', encoding="utf-8")
        got = self.preprocess(a.read_text(encoding="utf-8"), a)
        self.assertIn("B", got)
        self.assertIn('{% include-markdown "b.md" %}', got)
        self.assertTrue(got.endswith(" A"))

    def test_missing_snippet_left_as_is(self):
        content = '{% include-markdown "snippets/absent.md" %}'
        got = self.preprocess(content)
        self.assertIn("{% include-markdown", got)

    def test_non_include_block_untouched(self):
        content = "{% if product %} да {% endif %}"
        got = self.preprocess(content)
        self.assertEqual(got, content)

    def test_whitespace_trimmed_but_surrounding_kept(self):
        snippet = self.docs_dir / "s.md"
        snippet.write_text("\n\nтекст\n\n", encoding="utf-8")
        content = "до\n{% include-markdown \"s.md\" %}\nпосле"
        got = self.preprocess(content)
        self.assertIn("\nтекст\n", got)


# -----------------------------------------------------------------------------
# process() — сквозной прогон на временном docs_dir
# -----------------------------------------------------------------------------

class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, files: dict[str, str]):
        docs_dir = make_docs(self.root, files)
        out_dir = self.root / "out"
        pi.process(docs_dir, out_dir)
        return docs_dir, out_dir

    def test_common_case(self):
        _, out = self._run(
            {
                "index.md": (
                    "Главная\n\n"
                    '{%\n'
                    '    include-markdown "snippets/hello.md"\n'
                    '    start="<!--s-->"\n'
                    '    end="<!--e-->"\n'
                    '%}\n'
                ),
                "snippets/hello.md": (
                    "/*s-вырезается*/\n"
                    "<!--s-->\n"
                    "Содержимое сниппета\n"
                    "<!--e-->\n"
                    "/*e-вырезается*/\n"
                ),
                "other/page.md": "Ещё страница\n",
            }
        )
        expanded = (out / "index.md").read_text(encoding="utf-8")
        self.assertIn("Содержимое сниппета", expanded)
        self.assertNotIn("include-markdown", expanded)
        self.assertNotIn("{", expanded)
        self.assertIn(
            "Содержимое сниппета",
            (out / "snippets" / "hello.md").read_text(encoding="utf-8"),
        )
        self.assertTrue((out / "other" / "page.md").exists())

    def test_urls_rewritten_towards_output(self):
        _, out = self._run(
            {
                "pages/index.md": (
                    "Страница\n\n"
                    '{% include-markdown "../snippets/box.md" %}'
                ),
                "snippets/box.md": "![скрин](../assets/pic.png)\n",
                "assets/pic.png": b"\x89PNG\x0d\x0a\x1a\x0a",
            }
        )
        expanded = (out / "pages" / "index.md").read_text(encoding="utf-8")
        self.assertIn("](../assets/pic.png)", expanded)
        self.assertNotIn("include-markdown", expanded)

    def test_include_inline_preserves_code(self):
        code = "Код сниппета {x}"
        _, out = self._run(
            {
                "page.md": '{% include-markdown "snippets/c.md" %}',
                "snippets/c.md": code,
            }
        )
        self.assertIn(code, (out / "page.md").read_text(encoding="utf-8"))

    def test_out_dir_recreated_from_scratch(self):
        docs_dir = make_docs(
            self.root, {"index.md": "Одна версия\n"}
        )
        out_dir = self.root / "out"
        pi.process(docs_dir, out_dir)
        first = (out_dir / "index.md").read_text(encoding="utf-8")
        self.assertEqual(first, "Одна версия\n")

        (docs_dir / "index.md").write_text(
            'Другая версия {% include-markdown "s.md" %}\n', encoding="utf-8"
        )
        (docs_dir / "s.md").write_text("сниппет", encoding="utf-8")
        pi.process(docs_dir, out_dir)
        second = (out_dir / "index.md").read_text(encoding="utf-8")
        self.assertIn("сниппет", second)
        self.assertNotIn("include-markdown", second)

    def test_non_md_files_copied(self):
        _, out = self._run(
            {
                "index.md": "# Документ\n",
                "assets/pic.png": b"\x89PNG\x0d\x0a\x1a\x0a \x01\x02",
                "styles/site.css": "body { color: red; }\n",
            }
        )
        self.assertEqual(
            (out / "assets" / "pic.png").read_bytes(),
            b"\x89PNG\x0d\x0a\x1a\x0a \x01\x02",
        )
        self.assertEqual(
            (out / "styles" / "site.css").read_text(encoding="utf-8"),
            "body { color: red; }\n",
        )


# -----------------------------------------------------------------------------
# sync_zensical_config() — пересоздание zensical/mkdocs.zensical.yml
# -----------------------------------------------------------------------------

class SyncConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old_src = pi.SRC_CONFIG
        self._old_zcfg = pi.ZENSICAL_CONFIG
        self._old_out = pi.OUT_DIR
        pi.SRC_CONFIG = self.root / "mkdocs.yml"
        pi.ZENSICAL_CONFIG = self.root / "mkdocs.zensical.yml"
        pi.OUT_DIR = self.root / "zensical" / "build" / "docs_expanded"

    def tearDown(self):
        pi.SRC_CONFIG = self._old_src
        pi.ZENSICAL_CONFIG = self._old_zcfg
        pi.OUT_DIR = self._old_out
        self.tmp.cleanup()

    def _write_src(self, text: str) -> None:
        pi.SRC_CONFIG.write_text(text, encoding="utf-8")

    def _rendered(self) -> str:
        return pi._render_zensical_config(pi.SRC_CONFIG, pi.ZENSICAL_CONFIG)

    def test_first_run_creates_file(self):
        self._write_src("site_name: Тест\ndocs_dir: docs\n")
        self.assertTrue(pi.sync_zensical_config())
        self.assertTrue(pi.ZENSICAL_CONFIG.exists())
        self.assertIn("docs_dir: ", pi.ZENSICAL_CONFIG.read_text(encoding="utf-8"))

    def test_second_run_is_noop(self):
        self._write_src("site_name: Тест\n")
        self.assertTrue(pi.sync_zensical_config())
        mtime = pi.ZENSICAL_CONFIG.stat().st_mtime_ns
        self.assertFalse(pi.sync_zensical_config())
        self.assertEqual(pi.ZENSICAL_CONFIG.stat().st_mtime_ns, mtime)

    def test_changed_source_recreates(self):
        self._write_src("site_name: Старое\nnav: [a.md]\n")
        self.assertTrue(pi.sync_zensical_config())
        first = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        self.assertIn("Старое", first)

        self._write_src("site_name: Новое\nnav: [a.md, b.md]\n")
        self.assertTrue(pi.sync_zensical_config())
        second = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        self.assertIn("Новое", second)
        self.assertIn("b.md", second)

    def test_include_markdown_plugin_removed(self):
        self._write_src(
            "plugins:\n"
            "- search\n"
            "- include-markdown:\n"
            "    rewrite_relative_urls: true\n"
        )
        pi.sync_zensical_config()
        text = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        self.assertNotIn("include-markdown", text)
        self.assertIn("search", text)

    def test_glightbox_slide_effect_removed(self):
        self._write_src(
            "plugins:\n"
            "- glightbox:\n"
            "    slide_effect: slide\n"
            "    zoomable: true\n"
        )
        pi.sync_zensical_config()
        text = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        self.assertNotIn("slide_effect", text)
        self.assertIn("zoomable", text)

    def test_docs_dir_points_to_expanded(self):
        self._write_src("docs_dir: docs\n")
        pi.sync_zensical_config()
        text = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        expected = os.path.relpath(pi.OUT_DIR, pi.ZENSICAL_CONFIG.parent)
        self.assertIn(f"docs_dir: {expected}", text)

    def test_custom_dir_relative_to_dst(self):
        src_dir = self.root / "data"
        src_dir.mkdir()
        overrides = src_dir / "overrides"
        overrides.mkdir()
        pi.SRC_CONFIG = src_dir / "mkdocs.yml"
        pi.SRC_CONFIG.write_text("theme:\n  name: material\n  custom_dir: overrides\n", encoding="utf-8")
        pi.sync_zensical_config()
        text = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        expected = os.path.relpath(overrides.resolve(), pi.ZENSICAL_CONFIG.parent)
        self.assertIn(expected, text)
        self.assertNotIn("custom_dir: overrides\n", text)

    def test_toc_gets_unicode_slugify(self):
        self._write_src("markdown_extensions:\n- toc:\n    title: На этой странице\n")
        pi.sync_zensical_config()
        text = pi.ZENSICAL_CONFIG.read_text(encoding="utf-8")
        self.assertIn("slugify: !!python/name:markdown.extensions.toc.slugify_unicode", text)

    def test_generated_config_loads_with_zensical_loader(self):
        self._write_src(
            "site_name: Тест\n"
            "markdown_extensions:\n"
            "- toc:\n"
            "    title: На этой странице\n"
        )
        pi.sync_zensical_config()
        import yaml as _yaml
        loaded = _yaml.load(
            pi.ZENSICAL_CONFIG.read_text(encoding="utf-8"), Loader=_yaml.Loader
        )
        slugify = loaded["markdown_extensions"][0]["toc"]["slugify"]
        self.assertEqual(slugify("Привет Мир", "-"), "привет-мир")

    def test_nav_synced_from_source(self):
        self._write_src("nav:\n- a.md\n- Секция:\n  - b.md\n  - c.md\n")
        pi.sync_zensical_config()
        import yaml as _yaml
        loaded = _yaml.safe_load(pi.ZENSICAL_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(loaded["nav"], ["a.md", {"Секция": ["b.md", "c.md"]}])


# -----------------------------------------------------------------------------
# main() — через подмену глобальных констант
# -----------------------------------------------------------------------------

class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self._old_src = pi.SRC_CONFIG
        self._old_out = pi.OUT_DIR
        self._old_zcfg = pi.ZENSICAL_CONFIG
        pi.ZENSICAL_CONFIG = self.root / "mkdocs.zensical.yml"

    def tearDown(self):
        pi.SRC_CONFIG = self._old_src
        pi.OUT_DIR = self._old_out
        pi.ZENSICAL_CONFIG = self._old_zcfg
        self.tmp.cleanup()

    def test_main_builds_from_docs_config(self):
        docs_dir = self.root / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.md").write_text(
            '{% include-markdown "s.md" %}', encoding="utf-8"
        )
        (docs_dir / "s.md").write_text("содержимое", encoding="utf-8")
        cfg = self.root / "mkdocs.yml"
        cfg.write_text(f"docs_dir: docs\nsite_name: Тест\n", encoding="utf-8")

        pi.SRC_CONFIG = cfg
        pi.OUT_DIR = self.root / "out"

        code = pi.main()
        self.assertEqual(code, 0)
        self.assertEqual(
            (self.root / "out" / "index.md").read_text(encoding="utf-8"),
            "\nсодержимое",
        )

    def test_main_errors_when_docs_dir_missing(self):
        cfg = self.root / "mkdocs.yml"
        cfg.write_text("docs_dir: missing\n", encoding="utf-8")
        pi.SRC_CONFIG = cfg
        pi.OUT_DIR = self.root / "out"
        self.assertEqual(pi.main(), 1)
        self.assertFalse(pi.OUT_DIR.exists())


if __name__ == "__main__":
    unittest.main()