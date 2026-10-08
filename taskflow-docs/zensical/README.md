# Zensical — препроцессор `{% include-markdown %}` для сборки документации

Учебно-демонстрационный проект: сборка документации TaskFlow
(обычный MkDocs Material-сайт со сниппетами) альтернативным
генератором статических сайтов — [Zensical](https://zensical.dev/).

Изюминка: Zensical не умеет плагин `mkdocs-include-markdown-plugin`,
поэтому сниппеты здесь раскрывает написанный вручную препроцессор
`process_includes.py`, а конфиг для Zensical генерируется из
стандартного `mkdocs.yml` автоматически.

## Что внутри

| Файл | Назначение |
|---|---|
| `process_includes.py` | Препроцессор: раскрывает `{% include-markdown %}` и синхронизирует конфиг Zensical |
| `mkdocs.zensical.yml` | Адаптированная копия `mkdocs.yml` (генерируется скриптом) |
| `tests/test_process_includes.py` | Юнит-тесты (только стандартная библиотека) |
| `build/docs_expanded/` | Результат препроцессинга (исключён из git) |
| `site/` | Собранный Zensical-сайт (исключён из git) |

## Зачем это нужно

В `docs/` сниппеты подключаются блоками:

```markdown
{% include-markdown "snippets/auth-note.md" %}
```

MkDocs раскрывает их плагином `mkdocs-include-markdown-plugin`.
Zensical этот плагин не поддерживает — без препроцессора блоки
попадали бы в HTML как сырой текст.

`process_includes.py` — «мост»: он читает исходники из `docs_dir`,
заменяет все `{% include-markdown %}` реальным содержимым сниппетов
и пишет результат в `build/docs_expanded/`. Исходники не изменяются —
скрипт только читает и копирует.

Поддерживаются возможности плагина:
- `start=` / `end=` — включить фрагмент сниппета между
  HTML-маркерами (повторная логика `filter_inclusions()` плагина);
- переписывание относительных ссылок под место вставки
  (аналог `rewrite_relative_urls: true` — картинки `../assets/...`
  и ссылки `../admin-guide/users.md` остаются валидными);
- рекурсивное раскрытие вложенных сниппетов с защитой от циклов;
- копирование не-Markdown файлов (картинки, PDF и т.п.) без изменений.

## Как запустить

Требуется Python 3.12+ с PyYAML и установленный Zensical
(`pip install zensical`), например:

```bash
source ~/zensical/.venv/bin/activate   # установленное окружение
```

**1. Раскрыть сниппеты и синхронизировать конфиг (из корня репозитория):**

```bash
python3 zensical/process_includes.py
```

Скрипт читает `mkdocs.yml`, определяет `docs_dir` и параметры плагина
`include-markdown`, раскрывает сниппеты в `zensical/build/docs_expanded/`.
Если `zensical/mkdocs.zensical.yml` отстал от `mkdocs.yml` — скрипт
пересоздаёт его автоматически (строка `> обновлён конфиг Zensical: ...`).

С опцией `--pdfs` (или `-p`) дополнительно генерируются PDF всех страниц
`nav` (`avto_doc` + headless LibreOffice) в
`build/docs_expanded/assets/pdf/` — их Zensical перенесёт в собранный
сайт, и кнопка «Скачать в PDF» заработает:

```bash
python3 zensical/process_includes.py --pdfs
```

PDF-генерации нужен LibreOffice в PATH (`soffice`) и Python-пакеты
`pypdf`, `python-docx` (в реальном пайплайне на GitHub Pages ту же
работу делает хук `hooks/generate_pdf.py` при сборке MkDocs).

**2. Собрать сайт:**

```bash
zensical build -f zensical/mkdocs.zensical.yml
```

Проверка сборки в строгом режиме:

```bash
zensical build -f zensical/mkdocs.zensical.yml -s
```

**3. Посмотреть локально:**

```bash
zensical serve -f zensical/mkdocs.zensical.yml
# откройте http://localhost:8000
```

Собранный сайт появляется в `zensical/site/`.

## Файл mkdocs.zensical.yml

Адаптированная копия `mkdocs.yml` для Zensical. Отличия от оригинала:

1. Плагин `include-markdown` убран: сниппеты уже раскрыты
   препроцессором.
2. `docs_dir` указывает на `build/docs_expanded` — результат
   препроцессинга (Zensical резолвит пути относительно папки конфига).
3. `custom_dir` темы переписан в `../overrides` (конфиг лежит в
   `zensical/`, кастомизация темы — в `overrides/` у корня репозитория).
4. В `toc` добавлен `slugify: !!python/name:markdown.extensions.toc.slugify_unicode`
   — кириллические якоря формируются «читаемо» (без `_6`).
5. Тег `!ENV` из `git-revision-date-localized` (например,
   `enabled: !ENV [CI, false]`) разрешается в обычное значение
   переменной окружения.

Файл не правится руками: при каждом запуске `process_includes.py`
он сверяется с актуальным `mkdocs.yml` и пересоздаётся только при
расхождениях. Теги `!!python/name:` сериализуются корректно
(используются для `slugify` и emoji-индексов pymdownx).

## Тесты

Юнит-тесты на `unittest` (без дополнительных зависимостей):

```bash
python3 -m unittest discover -s zensical/tests
```

Покрытие: парсинг блоков, фильтрация `start`/`end`, переписывание
ссылок, вложенные сниппеты и защита от циклов, копирование
не-Markdown файлов, регенерация конфига (включая idempotent-
поведение) и вызовы `process()`/`main()` на временных фикстурах.

## Как это устроено внутри

- `_BLOCK_RE` разбирает блок `{% ... %}`;
- `_resolve_include_path()` повторяет логику плагина: пути `./`
  и `../` резолвятся от файла-включателя, остальные — от `docs_dir`;
- `_filter_inclusion()` повторяет `filter_inclusions()` плагина;
- `_rewrite_relative_urls()` переписывает md-ссылки, `<img>` и `<a>`;
- `_adapt_config()` + `_ZensicalDumper` превращают `mkdocs.yml`
  в `mkdocs.zensical.yml`, сохраняя теги `!!python/name:` и
  понимая тег `!ENV`;
- `process()` копирует дерево `docs_dir` с раскрытием и переносит
  остальные файлы без изменений.