#!/usr/bin/env python3
"""
Раскрывает сниппеты {% include-markdown %} в обычный Markdown.

Что делает и зачем
==================

Zensical не поддерживает плагин mkdocs-include-markdown-plugin
(сниппеты `{% include-markdown "файл" start=... end=... %}` не
подставляются, вместо них в HTML попадает сырой текст блока).

Этот скрипт — «мост»: он просматривает исходные страницы в
`docs_dir`, находит все блоки `{% include-markdown %}` и заменяет
их реальным содержимым сниппетов, записывая результат в отдельную
рабочую папку. После этого Zensical собирает сайт уже без
include-markdown — как обычные Markdown-файлы.

Исходники не изменяются: скрипт читает и копирует, а правки пишет
только в выходную папку.

Поведение повторяет настройки плагина из mkdocs.yml (см. SRC_CONFIG):
- `start` / `end` — включение только фрагмента сниппета между
  HTML-маркерами (строка с маркером не копируется);
- `rewrite_relative_urls` — относительные ссылки в сниппете
  переписываются так, чтобы они оставались валидными из места
  вставки (картинки `../assets/...` и ссылки на страницы);
- рекурсивное раскрытие вложенных сниппетов (с защитой от циклов).

Как запускать
-------------

    python3 zensical/process_includes.py

С опцией `--pdfs` (или `-p`) дополнительно генерируются PDF всех
страниц из nav (через DOCX и LibreOffice) в `build/docs_expanded/assets/pdf/`:

    python3 zensical/process_includes.py --pdfs

Результат появится в папке `zensical/build/docs_expanded/`
(рядом с этим скриптом). Затем:

    zensical build -f zensical/mkdocs.zensical.yml

Настройки (переменные в разделе CONFIG ниже):
- REPO_ROOT  — корень репозитория документации;
- SRC_CONFIG — путь к конфигу MkDocs, откуда берутся docs_dir
               и настройки include-markdown;
- OUT_DIR    — куда складывать раскрытые страницы.

Зависимости: PyYAML (есть в окружении Zensical).
"""

from __future__ import annotations

import copy
import os
import re
import shutil
import sys
from pathlib import Path

import yaml
from yaml.nodes import ScalarNode

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
"""Корень репозитория документации (верхняя папка с git-репозиторием)."""

SRC_CONFIG = REPO_ROOT / "mkdocs.yml"
"""Исходный конфиг MkDocs — источник docs_dir и плагина include-markdown."""

OUT_DIR = Path(__file__).resolve().parent / "build" / "docs_expanded"
"""Выходная папка с раскрытыми страницами (будет создана/очищена)."""

ZENSICAL_CONFIG = Path(__file__).resolve().parent / "mkdocs.zensical.yml"
"""Адаптированная копия SRC_CONFIG для сборки Zensical.

Скрипт сверяет его с SRC_CONFIG и пересоздаёт, если конфиг отстал.
"""

# Комментарий в NAV. Заменяется при сборке
NAV_COMMENT = "<!-- zensical: include-markdown раскрыт автоматически -->"

# -----------------------------------------------------------------------------
# YAML-загрузчик
# -----------------------------------------------------------------------------

class _YamlLoader(yaml.SafeLoader):
    """SafeLoader с поддержкой mkdocs-тегов.

    В конфигах MkDocs встречаются выражения вида
    `enabled: !ENV [CI, false]` (значение из переменной окружения CI
    или запасное значение, если переменная не задана), а также теги
    `!!python/name:module.attr` (emoji-индексы, slugify для toc).
    Без обработки yaml.safe_load падает с ConstructorError, поэтому
    теги разрешаются до обычных значений, а python/name — до пары
    (module, attr), которую умеет снова сериализовать _ZensicalDumper.
    """


def _construct_env(loader: _YamlLoader, node: yaml.Node):
    import os

    if isinstance(node, yaml.SequenceNode):
        parts = loader.construct_sequence(node)
        name = parts[0] if parts else ""
        default = parts[1] if len(parts) > 1 else ""
    else:
        name = loader.construct_scalar(node)
        default = ""
    return os.environ.get(name, default)


def _construct_python_name(
    loader: _YamlLoader, suffix: str, node: yaml.Node
) -> tuple[str, str] | str:
    """Представляет `!!python/name:module.attr` как пару (module, attr).

    Значение узла при теге `!!python/name:...` пустое — имя лежит в
    суффиксе тега (`material.extensions.emoji.twemoji`).
    """
    name = suffix
    if "." in name:
        module, attr = name.rsplit(".", 1)
        return (module, attr)
    return name


_YamlLoader.add_constructor("!ENV", _construct_env)
_YamlLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:", _construct_python_name
)


def _yaml_load(path: Path):
    """Читает YAML-конфиг, понимая тег `!ENV`."""
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_YamlLoader)

# -----------------------------------------------------------------------------
# Генерация zensical/mkdocs.zensical.yml из mkdocs.yml
# -----------------------------------------------------------------------------

# Соответствие значений `slugify` в оригинальном конфиге -> того же
# значения в Zensical-конфиге. В YAML теги python/name сериализуются
# вручную (см. _repr_python_name), т.к. yaml не умеет их дампить.
_SLUGIFY_OBJECT = ("markdown.extensions.toc", "slugify_unicode")


def _dump_python_name(dumper: yaml.Dumper, data: tuple[str, str]) -> ScalarNode:
    """Представляет (module, attr) как YAML-тег !!python/name:module.attr."""
    name = f"{data[0]}.{data[1]}"
    return ScalarNode("tag:yaml.org,2002:python/name:" + name, "", style=None)


class _ZensicalDumper(yaml.SafeDumper):
    pass


_ZensicalDumper.add_representer(tuple, _dump_python_name)


def _adapt_config(cfg: dict, src_config: Path, dst_config: Path) -> dict:
    """Адаптирует исходный mkdocs.yml под Zensical (правила из README).

    - убирает плагин include-markdown (сниппеты уже раскрыты скриптом);
    - убирает `slide_effect` из glightbox (Zensical не совместим);
    - переписывает `custom_dir` темы относительно корня Zensical;
    - добавляет `docs_dir` на папку с раскрытыми страницами;
    - добавляет unicode-slugify для toc (кириллические якоря).
    """
    out = copy.deepcopy(cfg)

    out["plugins"] = [
        p
        for p in out.get("plugins", [])
        if not (isinstance(p, dict) and "include-markdown" in p)
    ]
    for p in out["plugins"]:
        if isinstance(p, dict) and "glightbox" in p:
            p["glightbox"].pop("slide_effect", None)

    if isinstance(out.get("theme"), dict) and out["theme"].get("custom_dir"):
        custom_abs = (src_config.parent / out["theme"]["custom_dir"]).resolve()
        out["theme"]["custom_dir"] = os.path.relpath(
            custom_abs, dst_config.parent
        ).replace("\\", "/")

    for ext in out.get("markdown_extensions", []):
        if isinstance(ext, dict) and "toc" in ext:
            ext["toc"]["slugify"] = _SLUGIFY_OBJECT

    out["docs_dir"] = os.path.relpath(OUT_DIR, dst_config.parent).replace(
        "\\", "/"
    )
    return out


def _render_zensical_config(src_config: Path, dst_config: Path) -> str:
    """Возвращает текст zensical-конфига, полученный из src_config."""
    cfg = _yaml_load(src_config)
    adapted = _adapt_config(cfg, src_config, dst_config)
    text = yaml.dump(
        adapted,
        Dumper=_ZensicalDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    # PyYAML сериализует пустое значение тега python/name как `''`;
    # убираем лишний суффикс, чтобы получить каноничную запись
    # `slugify: !!python/name:module.attr`.
    return re.sub(r"(!!python/name:\S+) ''", r"\1", text)


def sync_zensical_config() -> bool:
    """Пересоздаёт zensical/mkdocs.zensical.yml, если он отстал.

    Возвращает True, если файл был переписан; False, если он уже актуален.
    """
    rendered = _render_zensical_config(SRC_CONFIG, ZENSICAL_CONFIG)
    try:
        current = ZENSICAL_CONFIG.read_text(encoding="utf-8")
    except FileNotFoundError:
        current = None
    if current == rendered:
        return False
    ZENSICAL_CONFIG.write_text(rendered, encoding="utf-8")
    print(f"  > обновлён конфиг Zensical: {ZENSICAL_CONFIG}")
    return True

# -----------------------------------------------------------------------------
# Парсинг блока include-markdown
# -----------------------------------------------------------------------------

# Блок: {%\n    include-markdown "путь"\n    start="..."\n    end="..."\n%}
_BLOCK_RE = re.compile(
    r"{%(?P<body>.*?)%}",
    re.DOTALL,
)

_PATH_RE = re.compile(r'include-markdown\s+"(?P<path>[^"]+)"')
_OPT_RE = re.compile(r'(?m)^\s*(?P<key>\w+)\s*=\s*"(?P<val>[^"]*)"')


def _is_url(string: str) -> bool:
    """True, если строка — URL со схемой (как is_url() в плагине).

    Распознаёт не только `scheme://`, но и `mailto:`, `tel:`, `data:`
    и т.п. — любой префикс из валидных символов схемы до первого `:`.
    Исключение — «C:» и однобуквенные префиксы (диски Windows).
    """
    i = string.find(":")
    if i <= 1:
        return False
    return all(c.isalnum() or c in "+-." for c in string[:i])


def _is_relative_path(path: str) -> bool:
    """True, если путь начинается с ./ или ../."""
    return (
        path.startswith("./")
        or path.startswith("../")
    )


def _resolve_include_path(raw: str, includer: Path, docs_dir: Path) -> Path:
    """Резолвит путь сниппета как это делает include-markdown."""
    if _is_relative_path(raw):
        base = includer.parent
    else:
        base = docs_dir
    candidate = base / raw
    return candidate.resolve()


def _filter_inclusion(
    text: str,
    start: str | None,
    end: str | None,
) -> str:
    """Возвращает фрагмент сниппета между маркерами start/end.

    Повторяет filter_inclusions() из mkdocs-include-markdown-plugin:
    маркеры в результат не попадают, поддерживаются повторения
    (берётся всё между каждой парой start/end).
    """
    if start is not None and end is None:
        if start not in text:
            return ""
        return text.split(start, maxsplit=1)[1]
    if start is None and end is not None:
        if end not in text:
            return text
        return text.split(end, maxsplit=1)[0]
    if start is not None and end is not None:
        if start not in text:
            start_part = [text]
        else:
            start_part = text.split(start)[1:]
        result = ""
        for chunk in start_part:
            for i, part in enumerate(chunk.split(end)):
                if not i % 2:
                    result += part
        return result
    return text


def _rewrite_relative_urls(markdown: str, src: Path, dst: Path) -> str:
    """Переписывает относительные URL сниппета под место вставки.

    Реализация повторяет rewrite_relative_urls() из
    mkdocs-include-markdown-plugin.
    """
    # Нормализуем пути до расчёта relpath: include_path резолвится
    # (Path.resolve()), а current_file — нет, и на macOS это даёт
    # расхождение /var -> /private/var, ломающее relpath.
    src_dir = os.path.dirname(os.fspath(Path(src).resolve()))
    dst_dir = os.path.dirname(os.fspath(Path(dst).resolve()))

    is_url = lambda u: _is_url(u)
    is_absolute = lambda u: u.startswith("/")
    is_anchor = lambda u: u.startswith("#")

    def rewrite(url: str) -> str:
        if is_url(url) or is_absolute(url) or is_anchor(url):
            return url
        new_path = os.path.relpath(
            os.path.join(src_dir, url),
            dst_dir,
        ).replace("\\", "/")
        if url.endswith("/"):
            new_path += "/"
        return new_path

    # md-ссылки [текст](url) и картинки ![alt](url)
    def md_link(m: re.Match) -> str:
        if not m.group(1):
            return m.group(0)
        return m.group(0)[: m.start(1) - m.start(0)] + rewrite(
            m.group(1)
        ) + m.group(0)[m.end(1) - m.start(0):]

    markdown = re.sub(r"\]\(([^#][^)]*)\)", md_link, markdown)
    markdown = re.sub(
        r'(<img\s+[^>]*?src\s*=\s*["\'])([^"\'#]+)(["\'])',
        lambda m: m.group(1) + rewrite(m.group(2)) + m.group(3),
        markdown,
    )
    # html ссылки <a href="url">
    markdown = re.sub(
        r'(<a\s+[^>]*?href\s*=\s*["\'])([^"\'#]+)(["\'])',
        lambda m: m.group(1) + rewrite(m.group(2)) + m.group(3),
        markdown,
    )
    return markdown


# -----------------------------------------------------------------------------
# Раскрытие одного блокa
# -----------------------------------------------------------------------------

def _read_snippet(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"  ! сниппет не найден: {path}")
        return None


def _preprocess_markdown(
    content: str,
    current_file: Path,
    docs_dir: Path,
    seen: set[Path],
    rewrite_urls: bool,
) -> str:
    """Заменяет все {% include-markdown %} внутри строки."""
    seen = set(seen)

    def repl(m: re.Match) -> str:
        body = m.group("body")
        if "include-markdown" not in body:
            return m.group(0)

        pm = _PATH_RE.search(body)
        if not pm:
            print(f"    ? не удалось распознать путь: {body[:80]!r}")
            return m.group(0)

        opts = {o.group("key"): o.group("val") for o in _OPT_RE.finditer(body)}
        raw_path = pm.group("path")
        include_path = _resolve_include_path(
            raw_path, current_file, docs_dir
        )

        if include_path in seen:
            print(f"    ! цикл сниппетов: {include_path}")
            return m.group(0)

        snippet = _read_snippet(include_path)
        if snippet is None:
            return m.group(0)

        filtered = _filter_inclusion(
            snippet,
            opts.get("start"),
            opts.get("end"),
        )

        if rewrite_urls:
            filtered = _rewrite_relative_urls(
                filtered, include_path, current_file
            )

        # Рекурсивное раскрытие вложенных include-markdown. seen
        # передаётся только в глубину (для защиты от циклов), а не
        # сохраняется для параллельных блоков в этой же строке.
        filtered = _preprocess_markdown(
            filtered, current_file, docs_dir, seen | {include_path}, rewrite_urls
        )
        return "\n" + filtered.rstrip("\n")

    return _BLOCK_RE.sub(repl, content)


# -----------------------------------------------------------------------------
# Копирование дерева с раскрытием
# -----------------------------------------------------------------------------

def _iter_python_files(docs_dir: Path):
    for root, _dirs, files in os.walk(docs_dir):
        for name in files:
            if name.endswith(".md"):
                yield Path(root) / name


def process(docs_dir: Path, out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    rewrite_urls = True
    mkdocs_rel = ""
    if SRC_CONFIG.exists():
        cfg = _yaml_load(SRC_CONFIG)
        for plugin in cfg.get("plugins", []):
            if isinstance(plugin, dict) and "include-markdown" in plugin:
                rewrite_urls = plugin["include-markdown"].get(
                    "rewrite_relative_urls", True
                )
        mkdocs_rel = (
            cfg["theme"].get("custom_dir", "")
            if isinstance(cfg.get("theme"), dict)
            else ""
        ) or ""

    total = 0
    blocks = 0
    for src in sorted(_iter_python_files(docs_dir)):
        rel = src.relative_to(docs_dir)
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        content = src.read_text(encoding="utf-8")
        total += 1
        b_before = content.count("include-markdown")
        new_content = _preprocess_markdown(
            content, src, docs_dir, set(), rewrite_urls
        )
        blocks += content.count("include-markdown")
        if b_before and "include-markdown" in new_content:
            left = new_content.count("include-markdown")
            print(f"  ? нераскрытые сниппеты {rel}: {left}")
        dst.write_text(new_content, encoding="utf-8")

    # Копируем прочие файлы (картинки, CSS и т.д.)
    for root, dirs, files in os.walk(docs_dir):
        if Path(root) == docs_dir and Path("__pycache__") in dirs:
            dirs.remove("__pycache__")
        for name in files:
            src = Path(root) / name
            if src.suffix == ".md":
                continue
            rel = src.relative_to(docs_dir)
            dst = out_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(src, dst)

    print(
        f"\nГотово: страниц {total}, блоков include-markdown {blocks}.\n"
        f"Результат: {out_dir}\n"
    )


# -----------------------------------------------------------------------------
# PDF-генерация (опция --pdfs)
# -----------------------------------------------------------------------------

PDF_ASSET_DIR = "assets/pdf"
"""Подпапка, куда генерация складывает PDF страниц документации."""


def postprocess_pdfs(docs_dir: Path, site_dir: Path) -> bool:
    """Генерирует PDF всех страниц nav из docs_dir в site_dir/assets/pdf/.

    Zensical не выполняет Python-хуки MkDocs, поэтому переиспользуется
    хук `hooks/generate_pdf.py`: он собирает DOCX (avto_doc) и
    конвертирует его в PDF через headless LibreOffice. На страницах
    сайта кнопка «Скачать в PDF» ищет файл по этому пути.

    Возвращает True, если PDF-генерация была запущена.
    """
    try:
        hooks_dir = REPO_ROOT / "hooks"
        sys.path.insert(0, str(hooks_dir))
        import logging

        logging.basicConfig(level=logging.INFO, format="%(message)s")
        import generate_pdf
    except Exception as exc:
        print(f"  ! PDF-генерация недоступна: {exc}")
        return False

    print("\nГенерация PDF страниц (avto_doc + LibreOffice)...")
    nav = _yaml_load(SRC_CONFIG).get("nav", [])
    config = {
        "docs_dir": str(docs_dir),
        "site_dir": str(site_dir),
        "nav": nav,
    }
    generate_pdf.on_post_build(config)
    pdfs = list((site_dir / PDF_ASSET_DIR).rglob("*.pdf"))
    print(f"Готово: PDF — {len(pdfs)}.\n")
    return True


def main(argv: list[str] | None = None) -> int:
    # docs_dir берётся из SRC_CONFIG (как это делает MkDocs:
    # относительно папки конфига). Если в конфиге нет docs_dir,
    # используется docs/ рядом с конфигом.
    argv = list(sys.argv if argv is None else argv)
    with_pdfs = "--pdfs" in argv or "-p" in argv

    cfg = _yaml_load(SRC_CONFIG)

    # Перед раскрытием сниппетов приводим конфиг сборки Zensical
    # в соответствие с mkdocs.yml.
    sync_zensical_config()

    docs_dir_name = cfg.get("docs_dir", "docs")
    docs_dir = (SRC_CONFIG.parent / docs_dir_name).resolve()
    if not docs_dir.exists():
        print(f"docs_dir не найден: {docs_dir}")
        return 1

    process(docs_dir, OUT_DIR)

    if with_pdfs:
        # PDF складываются в docs_expanded/assets/pdf и попадают в
        # собранный сайт вместе с остальными статичными файлами.
        postprocess_pdfs(docs_dir=OUT_DIR, site_dir=OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())