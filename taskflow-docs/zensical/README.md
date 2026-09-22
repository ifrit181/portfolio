# Zensical — эксперимент по запуску «Цифра.Карьер»

Здесь собраны результаты проверки генератора статических сайтов
[Zensical](https://zensical.dev/) как альтернативы MkDocs
для документации «Цифра.Карьер».

Папка исключена из git (см. `.gitignore`).

## Установка

Zensical установлен НЕ в git-репозитории, а отдельно:

- Расположение: `~/zensical`
- Виртуальное окружение: `~/zensical/.venv` (Python 3.12)
- Версия: 0.0.55 (`zensical --version`)

Активация:

```bash
source ~/zensical/.venv/bin/activate
```

Пробный проект (для знакомства) создан в `~/zensical`:
`zensical new .` → `zensical.toml`, `docs/`, `.github/`.

## Команды

```bash
# Сборка в папку site/
zensical build

# Локальный сервер
zensical serve
```

Полезные флаги:
- build: `-c/--clean`, `-s/--strict`
- serve: `-f/--config-file`, `-a/--dev-addr`, `-o/--open`

## Как запустить реальный проект документации

Zensical умеет читать конфиг MkDocs (`mkdocs.yml`), но с
ограничениями (см. ниже). Рабочий вариант — использовать
препроцессор `process_includes.py` + адаптированный конфиг:

**1. Раскрыть сниппеты include-markdown (обязательный шаг):**

```bash
cd /Users/tatanakudrasova/PycharmProjects/vist/user_manual
source ~/zensical/.venv/bin/activate
python3 zensical/process_includes.py
```

Скрипт читает `data/docs`, заменяет все `{% include-markdown %}`
реальным содержимым сниппетов и складывает результат в
`zensical/build/docs_expanded/`. Исходники не изменяются.

**2. Собрать сайт:**

```bash
zensical build -f zensical/mkdocs.zensical.yml
```

Команда собирает сайт за ~37-46 секунд (3 предупреждения о
битых якорях/страницах в исходниках, не связаны с Zensical).

**3. Посмотреть сайт — локальный сервер:**

```bash
zensical serve -f zensical/mkdocs.zensical.yml
```

Открыть в браузере: **http://localhost:8000**

Сервер работает в фоне и пересобирает сайт при изменениях
файлов в `data/docs`. Остановить — `Ctrl+C`.

Либо открыть собранную страницу напрямую без сервера:

```bash
open site/index.html
```

⚠️ При открытии через `file://` поиск и часть скриптов могут не
работать (сайт собран под HTTP), поэтому для полноценного
просмотра лучше использовать `zensical serve`.

⚠️ Важно: адрес `http://localhost:8000` в инструкциях Zensical —
просто подсказка для браузера, в команду его писать НЕ нужно
(zsh воспринимает `(http://...)` как атрибуты файла).

## Скрипт process_includes.py

**Что это:** препроцессор-мост для сниппетов `{% include-markdown %}`.

**Зачем нужен:** Zensical не поддерживает плагин
`mkdocs-include-markdown-plugin` — его блоки в тексте (998 вызовов
с `start/end` и 499 полных включений в 312 из 1162 файлов) не
подставляются и попадают в HTML как сырой текст.

**Что делает:**
- находит все блоки `{% include-markdown "файл" start=... end=... %}`
  и подставляет содержимое сниппета (целиком или фрагмент между
  HTML-маркерами), повторяя логику `filter_inclusions()` плагина;
- переписывает относительные ссылки в сниппетах под место вставки
  (аналог `rewrite_relative_urls: true` — картинки `../assets/...`
  и ссылки на страницы остаются валидными);
- рекурсивно раскрывает вложенные сниппеты с защитой от циклов;
- копирует не-Markdown файлы (картинки, CSS) без изменений;
- пишет результат в `zensical/build/docs_expanded/`, не трогая
  исходную `data/docs`.

**Настройки** — переменные в начале файла (`REPO_ROOT`, `SRC_CONFIG`,
`OUT_DIR`).

## Тесты

Юнит-тесты (стандартный `unittest`, без дополнительных зависимостей)
лежат в `zensical/tests/test_process_includes.py`. Покрывают парсинг
блоков, фильтрацию по `start`/`end`, переписывание ссылок, рекурсивное
раскрытие с защитой от циклов, копирование не-Markdown файлов и вызов
`process()`/`main()` на временных фикстурах.

Запуск (из корня репозитория):

```bash
source ~/zensical/.venv/bin/activate
python3 -m unittest discover -s zensical/tests
# подробно:
python3 -m unittest discover -s zensical/tests -v
```

## Файл mkdocs.zensical.yml

Адаптированная копия `data/mkdocs.yml`. Отличия от оригинала:
1. Убран `slide_effect: slide` из плагина glightbox (несовместим).
2. `docs_dir` указывает на `build/docs_expanded` — папку после
   препроцессинга (Zensical резолвит пути от корня проекта).
3. `custom_dir` переписан на `../data/overrides` (конфиг лежит в
   `zensical/`, а кастомизация темы — в `data/overrides`).
4. Плагин `include-markdown` убран (сниппеты уже раскрыты).

Файл не поддерживается руками: при запуске `process_includes.py`
`data/mkdocs.yml` адаптируется под Zensical и сравнивается с текущим
`mkdocs.zensical.yml`. Если конфиг отстал (например, изменился `nav`
или настройки), скрипт пересоздаёт его автоматически (строка
`> обновлён конфиг Zensical: ...`). Если совпадает — файл не трогается.

## Несовместимости с текущим mkdocs.yml

| Проблема | Статус / решение |
|---|---|
| Плагин `glightbox` с параметром `slide_effect` | Несовместим. Zensical знает только: `touchNavigation`, `loop`, `effect`, `width`, `height`, `zoomable`, `draggable`, `auto_themed`, `auto_caption`, `caption_position`, `background`, `shadow`, `manual`. Параметр `slide_effect: slide` вызывает `TypeError: GlightboxConfig.__init__() got an unexpected keyword argument 'slide_effect'` |
| `docs_dir` не задан в mkdocs.yml | Zensical резолвит пути относительно КОРНЯ проекта (папки конфига), а не самого конфига. Для `data/mkdocs.yml` нужно явно указать `docs_dir: data/docs` |
| `custom_dir: overrides` (кастомизация темы Material) | Нужно указывать относительно корня: `data/overrides` |
| Плагин `include-markdown` | **НЕ поддерживается напрямую**. Решение — препроцессор `process_includes.py`, раскрывающий сниппеты в `zensical/build/docs_expanded/` до сборки |

Критический блокер `include-markdown` снят: все 499 блоков (998
вызовов) раскрываются скриптом, и сайт собирается целиком.

## Не проверено / возможные пути дальше

- Альтернатива препроцессору — перевод сниппетов на `pymdownx.snippets`
  (поддерживается Zensical нативно: `--8<-- "путь"` и секции
  `--8<-- [start:имя]` / `--8<-- [end:имя]`). Тогда шаг препроцессинга
  не нужен, но придётся переписать ~1500 вызовов и маркеры в сниппетах.
- Тема Material и кастомная схема `zyfra_light` в настройках
  темы — внешний вид собранного сайта детально не сверялся.
- Поведение плагина `autolinks` (Zensical имеет собственный
  механизм автоссылок через расширение links).

## История проверки

- 0.0.55: тестовый проект в `~/zensical` собирается без ошибок.
- 0.0.55: реальный проект по `data/mkdocs.yml` — упал на glightbox.
- 0.0.55: экспериментальная сборка без препроцессинга
  (`docs_dir` + `custom_dir` + без `slide_effect`): сниппеты
  include-markdown остались нераскрытыми (сырой текст в HTML).
- 0.0.55: `process_includes.py` раскрывает все 499 блоков (0
  нераскрытых), сборка `zensical/mkdocs.zensical.yml` — успешно
  (~37 с, 3 предупреждения в исходниках, не связаны с Zensical).