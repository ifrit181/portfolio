"""Проверка соблюдения ГОСТ для собранных PDF и отчёт о расхождениях.

Для каждого собранного документа выполняется набор проверок
(титульный лист, структура, аннотация, обязательные разделы, колонтитулы,
метаданные, посторонний контент из шаблонов). Результаты складываются в
`DocReport`, а `build_report()` собирает из них markdown-файл
`site/assets/pdf-gost/check-report.md`.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

import doc_types
from gost_styles import RENAME

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"

_LEVEL_RANK = {OK: 0, WARN: 1, FAIL: 2}

# Строки-индикаторы данных, унаследованных от primer.docx — их быть не должно.
FORBIDDEN_TEXTS = (
    "Качество на складах",
    "Vladimir Korychev",
    "Щёлкните правой кнопкой",
    "Группа компаний «Цифра»",
    'Группа компаний "Цифра"',
    "Данный документ является интеллектуальной собственностью",
    "Соколов В.В.",
    "Sokolov",
)

FORBIDDEN_AUTHORS = {"Vladimir Korychev", "Соколов В.В.", "Sokolov"}


@dataclass
class Finding:
    level: str
    group: str
    message: str


@dataclass
class DocReport:
    rel: str
    out: str = ""
    pages: int | None = None
    doc_type: str = ""
    standard: str = ""
    findings: list[Finding] = field(default_factory=list)
    error: str = ""

    @property
    def level(self) -> str:
        if self.error:
            return FAIL
        level = OK
        for f in self.findings:
            if _LEVEL_RANK[f.level] > _LEVEL_RANK[level]:
                level = f.level
        return level

    def count(self, level: str) -> int:
        return sum(1 for f in self.findings if f.level == level)

    def add(self, level: str, group: str, message: str) -> None:
        self.findings.append(Finding(level, group, message))


def _norm(text: str) -> str:
    return " ".join(str(text).replace("\u00a0", " ").split()).casefold()


def _has_line(text: str, target: str) -> bool:
    want = _norm(target)
    return any(_norm(ln) == want for ln in text.split("\n"))


def check_pdf(pdf_path: Path, ctx: dict, entries, rep: DocReport) -> None:
    """Выполнить все проверки PDF и дополнить *rep* результатами."""
    reader = PdfReader(str(pdf_path))
    rep.pages = len(reader.pages)
    if rep.pages == 0:
        rep.add(FAIL, "Структура", "PDF не содержит страниц")
        return

    texts = [(pg.extract_text() or "") for pg in reader.pages]
    full = "\n".join(texts)
    full_n = _norm(full)
    p1 = texts[0]

    # --- Титульный лист (ГОСТ 19.104-78) ---
    if _norm(p1).find("утверждено") >= 0:
        rep.add(OK, "Титул", "надпись «УТВЕРЖДЕНО» на первом листе")
    else:
        rep.add(FAIL, "Титул", "нет надписи «УТВЕРЖДЕНО» на первом листе")

    m = re.search(r"Листов\s+(\d+)", p1)
    if m:
        sheets = int(m.group(1))
        if sheets == rep.pages:
            rep.add(OK, "Титул", f"«Листов {sheets}» совпадает с числом страниц")
        else:
            rep.add(FAIL, "Титул",
                    f"«Листов {sheets}» != числу страниц ({rep.pages})")
    elif rep.pages == 1:
        rep.add(OK, "Титул", "«Листов N» не выводится при одном листе")
    else:
        rep.add(FAIL, "Титул", "нет строки «Листов N» на первом листе")

    doc_type = ctx["doc_type"]
    if _norm(doc_type.title) in _norm(p1):
        rep.add(OK, "Титул", f"вид документа «{doc_type.title}» на титуле")
    else:
        rep.add(WARN, "Титул", f"не найден вид документа «{doc_type.title}»")

    product = str(ctx.get("product_name_used") or "").strip()
    if product:
        if _norm(product) in _norm(p1):
            rep.add(OK, "Титул", f"наименование ПО «{product}» на титуле")
        else:
            rep.add(WARN, "Титул",
                    f"наименование ПО «{product}» не найдено на титуле")

    # --- Структура: содержание (ГОСТ Р 7.0.97-2016, п. 5.3) ---
    toc_idx = next((i for i, t in enumerate(texts) if _has_line(t, "Содержание")),
                   None)
    if toc_idx is None:
        rep.add(FAIL, "Структура", "нет страницы «СОДЕРЖАНИЕ»")
    else:
        rep.add(OK, "Структура",
                f"страница «СОДЕРЖАНИЕ» (лист {toc_idx + 1})")

        # Содержание может занимать несколько листов: подхватываем
        # идущие подряд листы с точечными выносками.
        toc_parts = []
        i = toc_idx
        while i < len(texts) and (i == toc_idx
                                  or re.search(r"\.{4,}", texts[i])):
            toc_parts.append(texts[i])
            i += 1
        toc_text = "\n".join(toc_parts)

        if entries:
            toc_n = _norm(toc_text)
            missing = []
            total = 0
            for _lvl, text in entries:
                target = _norm(RENAME.get(text, text))
                if not target:
                    continue
                total += 1
                if target not in toc_n:
                    missing.append(RENAME.get(text, text))
            if not missing:
                rep.add(OK, "Структура", f"все записи содержания найдены ({total})")
            else:
                shown = "; ".join(missing[:5])
                if len(missing) > 5:
                    shown += f"; … (всего {len(missing)})"
                rep.add(WARN, "Структура",
                        f"в содержании не найдено {len(missing)} из {total}: {shown}")

            if re.search(r"\.{4,}", toc_text):
                rep.add(OK, "Структура",
                        f"точечные выноски в содержании ({len(toc_parts)} лист.)")
            else:
                rep.add(WARN, "Структура", "не найдены точечные выноски в содержании")

    # --- Структура: лист регистрации изменений (ГОСТ 19.106-78) ---
    if any(_has_line(t, "Лист регистрации изменений") for t in texts):
        rep.add(OK, "Структура", "лист регистрации изменений присутствует")
    else:
        rep.add(FAIL, "Структура", "нет листа регистрации изменений")

    # --- Аннотация (ГОСТ 19.105-78, п. 1.6) ---
    annotation = str(ctx.get("annotation") or "").strip()
    if annotation:
        if any(_has_line(t, "Аннотация") for t in texts):
            rep.add(OK, "Аннотация", "страница «АННОТАЦИЯ» присутствует")
        else:
            rep.add(FAIL, "Аннотация",
                    "gost_annotation задан, но страница «АННОТАЦИЯ» не найдена")
    elif doc_type.info_part:
        rep.add(WARN, "Аннотация",
                f"gost_annotation не задана (обязательна для «{doc_type.title}»)")
    else:
        rep.add(OK, "Аннотация", "не требуется для этого вида документа")

    # --- Обязательные разделы ---
    headings = [t for lvl, t in (entries or []) if lvl <= 2]
    missing = doc_types.missing_sections(doc_type, headings)
    if doc_type.sections:
        if missing:
            rep.add(WARN, "Разделы",
                    f"нет обязательных разделов ({doc_type.content_standard}): "
                    + ", ".join(missing))
        else:
            rep.add(OK, "Разделы",
                    f"все обязательные разделы на месте "
                    f"({doc_type.content_standard}, {len(doc_type.sections)} шт.)")
    else:
        rep.add(OK, "Разделы", "состав разделов стандартом не нормируется")

    # --- Колонтитулы (ГОСТ 19.106-78, п. 2.1) ---
    body_texts = texts[1:]
    oboz = str(ctx.get("oboznachenie") or "").strip()
    if oboz:
        hits = sum(1 for t in body_texts if oboz in t)
        if hits:
            rep.add(OK, "Колонтитулы",
                    f"обозначение в шапке: {hits} из {len(body_texts)} листов (кроме титула)")
        else:
            rep.add(WARN, "Колонтитулы",
                    "обозначение из gost_oboznachenie не найдено в шапке")

    stroka = str(ctx.get("stroka_izmenenij") or "").strip()
    if stroka:
        hits = sum(1 for t in body_texts if stroka in t)
        if hits:
            rep.add(OK, "Колонтитулы",
                    f"строка изменений в футере: {hits} из {len(body_texts)} листов")
        else:
            rep.add(WARN, "Колонтитулы",
                    "строка из gost_stroka_izmenenij не найдена в футере")

    if rep.pages > 1:
        numbered = 0
        for i in range(1, rep.pages):
            lines = [ln.strip() for ln in texts[i].split("\n") if ln.strip()][:3]
            num = str(i + 1)
            if any(re.search(rf"(?<!\d){re.escape(num)}(?!\d)", ln)
                   for ln in lines):
                numbered += 1
        ratio = numbered / (rep.pages - 1)
        if ratio >= 0.9:
            rep.add(OK, "Колонтитулы",
                    f"нумерация страниц на {numbered}/{rep.pages - 1} листах")
        else:
            rep.add(WARN, "Колонтитулы",
                    f"нумерация страниц найдена только на {numbered}/"
                    f"{rep.pages - 1} листах")

    # --- Метаданные PDF ---
    meta = reader.metadata
    title = ((meta.title if meta else None) or "").strip()
    subject = ((meta.subject if meta else None) or "").strip()
    author = ((meta.author if meta else None) or "").strip()

    if not title:
        rep.add(FAIL, "Метаданные", "/Title пуст")
    elif product and _norm(title) != _norm(product):
        rep.add(WARN, "Метаданные",
                f"/Title «{title}» != наименованию ПО «{product}»")
    else:
        rep.add(OK, "Метаданные", f"/Title = «{title}»")

    if not subject:
        rep.add(FAIL, "Метаданные", "/Subject пуст")
    elif subject != doc_type.title:
        rep.add(WARN, "Метаданные",
                f"/Subject «{subject}» != виду документа «{doc_type.title}»")
    else:
        rep.add(OK, "Метаданные", f"/Subject = «{subject}»")

    if not author:
        rep.add(FAIL, "Метаданные", "/Author пуст")
    elif author in FORBIDDEN_AUTHORS:
        rep.add(FAIL, "Метаданные", f"/Author из шаблона: «{author}»")
    else:
        rep.add(OK, "Метаданные", f"/Author = «{author}»")

    # --- Посторонний контент из primer.docx ---
    found = [s for s in FORBIDDEN_TEXTS if s in full]
    if found:
        rep.add(FAIL, "Чужой контент",
                "обнаружены данные из шаблона primer.docx: " + "; ".join(found))
    else:
        rep.add(OK, "Чужой контент",
                f"данные из шаблонов не обнаружены "
                f"({len(FORBIDDEN_TEXTS)} строк-индикаторов)")


def build_report(reports: list[DocReport], *, timestamp: str,
                 only: str | None = None) -> str:
    """Собрать markdown-отчёт по всем DocReport."""
    total = len(reports)
    n_ok = sum(1 for r in reports if r.level == OK)
    n_warn = sum(1 for r in reports if r.level == WARN)
    n_fail = sum(1 for r in reports if r.level == FAIL)
    total_checks = sum(len(r.findings) for r in reports)
    total_warns = sum(r.count(WARN) for r in reports)
    total_fails = sum(r.count(FAIL) for r in reports)

    lines = [
        "# Отчёт проверки PDF по ГОСТ",
        "",
        f"- Дата сборки: {timestamp}",
        f"- Фильтр: {'все файлы' if not only else '`' + only + '`'}",
        f"- Документов: **{total}** — OK: **{n_ok}**, "
        f"с предупреждениями: **{n_warn}**, с ошибками: **{n_fail}**",
        f"- Проверок: **{total_checks}** — предупреждений: **{total_warns}**, "
        f"ошибок: **{total_fails}**",
        "",
        "## Сводка",
        "",
        "| # | Документ | PDF | Листов | OK | WARN | FAIL | Итог |",
        "|---:|---|---|---:|---:|---:|---:|:---:|",
    ]
    for i, r in enumerate(reports, 1):
        pages = str(r.pages) if r.pages is not None else "—"
        out = f"`{r.out}`" if r.out else "—"
        if r.error:
            ok = warn = "—"
            fails = "1"
            verdict = "FAIL"
        else:
            ok, warn, fails = str(r.count(OK)), str(r.count(WARN)), str(r.count(FAIL))
            verdict = r.level
        lines.append(f"| {i} | {r.rel} | {out} | {pages} | {ok} | {warn} "
                     f"| {fails} | **{verdict}** |")

    lines += ["", "## Расхождения", ""]
    divergences = []
    for r in reports:
        if r.error:
            divergences.append(f"- **FAIL** · {r.rel} — сборка не выполнена: {r.error}")
        for f in r.findings:
            if f.level != OK:
                divergences.append(f"- **{f.level}** · {r.rel} — {f.group}: {f.message}")
    lines += divergences or ["Расхождений не обнаружено."]

    lines += ["", "## Проверки по файлам", ""]
    for i, r in enumerate(reports, 1):
        lines.append(f"### {i}. {r.rel}")
        lines.append("")
        if r.doc_type:
            std = f" ({r.standard})" if r.standard else ""
            lines.append(f"- Вид документа: {r.doc_type}{std}")
        if r.out:
            lines.append(f"- Файл: `{r.out}`")
        if r.pages is not None:
            lines.append(f"- Листов: {r.pages}")
        lines.append(f"- Итог: **{r.level}**")
        lines.append("")
        if r.error:
            lines.append(f"- **FAIL** · Сборка: {r.error}")
            lines.append("")
            continue
        for f in r.findings:
            lines.append(f"- **{f.level}** · {f.group} · {f.message}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
