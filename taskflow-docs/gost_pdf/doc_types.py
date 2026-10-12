"""Виды (типы) документов и их обязательные разделы.

Источник: `reference/matrix.md` (ГОСТ 19.101-77, ГОСТ 19.201 … 19.507,
ГОСТ 34.201-2020, ГОСТ Р 59795-2021).

Тип документа задаётся в front-matter markdown-файла::

    ---
    gost_doc_type: rukovodstvo-polzovatelya
    ---

Допускаются русские алиасы («Руководство пользователя», «руководство
пользователя» и т. п.). По умолчанию — `rukovodstvo-polzovatelya`.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocType:
    key: str
    title: str                       # вид документа по ГОСТ
    code: str                        # код вида документа (ЕСПД / ГОСТ 34.201)
    content_standard: str            # стандарт, задающий содержание
    content_ref: str                 # пункт со списком разделов
    sections: tuple[str, ...] = field(default_factory=tuple)
    info_part: bool = False          # обязательна ли информационная часть
    aliases: tuple[str, ...] = field(default_factory=tuple)


def _dt(*args, **kwargs) -> DocType:
    return DocType(*args, **kwargs)


DOC_TYPES: dict[str, DocType] = {
    # --- ЕСПД: программные и эксплуатационные документы ---
    "tz": _dt(
        "tz", "Техническое задание", "01",
        "ГОСТ 19.201-78", "п. 1.4",
        sections=(
            "Введение",
            "Основания для разработки",
            "Назначение разработки",
            "Требования к программе или программному изделию",
            "Требования к программной документации",
            "Технико-экономические показатели",
            "Стадии и этапы разработки",
            "Порядок контроля и приемки",
        ),
        info_part=False,
        aliases=("техническое задание", "техзадание", "тз"),
    ),
    "spetsifikatsiya": _dt(
        "spetsifikatsiya", "Спецификация", "00",
        "ГОСТ 19.202-78", "п. 4",
        sections=("Документация", "Комплексы", "Компоненты"),
        info_part=False,
        aliases=("спецификация",),
    ),
    "programma-ispytanij": _dt(
        "programma-ispytanij", "Программа и методика испытаний", "51",
        "ГОСТ 19.301-79", "п. 1.2",
        sections=(
            "Объект испытаний",
            "Цель испытаний",
            "Требования к программе",
            "Требования к программной документации",
            "Состав и порядок испытаний",
            "Методы испытаний",
        ),
        info_part=False,
        aliases=("программа и методика испытаний",),
    ),
    "tekst-programmy": _dt(
        "tekst-programmy", "Текст программы", "12",
        "ГОСТ 19.401-78", "п. 3–4",
        sections=(),
        info_part=False,
        aliases=("текст программы",),
    ),
    "opisanie-programmy": _dt(
        "opisanie-programmy", "Описание программы", "13",
        "ГОСТ 19.402-78", "п. 3",
        sections=(
            "Общие сведения",
            "Функциональное назначение",
            "Описание логической структуры",
            "Используемые технические средства",
            "Вызов и загрузка",
            "Входные данные",
            "Выходные данные",
        ),
        info_part=True,
        aliases=("описание программы",),
    ),
    "poyasnitelnaya-zapiska": _dt(
        "poyasnitelnaya-zapiska", "Пояснительная записка", "81",
        "ГОСТ 19.404-79", "п. 1.2",
        sections=(
            "Введение",
            "Назначение и область применения",
            "Технические характеристики",
            "Ожидаемые технико-экономические показатели",
            "Источники, использованные при разработке",
        ),
        info_part=False,
        aliases=("пояснительная записка",),
    ),
    "opisanie-primeneniya": _dt(
        "opisanie-primeneniya", "Описание применения", "31",
        "ГОСТ 19.502-78", "п. 3",
        sections=(
            "Назначение программы",
            "Условия применения",
            "Описание задачи",
            "Входные и выходные данные",
        ),
        info_part=True,
        aliases=("описание применения",),
    ),
    "rukovodstvo-sistemnogo-programmista": _dt(
        "rukovodstvo-sistemnogo-programmista",
        "Руководство системного программиста", "32",
        "ГОСТ 19.503-79", "п. 1.2",
        sections=(
            "Общие сведения о программе",
            "Структура программы",
            "Настройка программы",
            "Проверка программы",
            "Дополнительные возможности",
            "Сообщения системному программисту",
        ),
        info_part=True,
        aliases=("руководство системного программиста",),
    ),
    "rukovodstvo-programmista": _dt(
        "rukovodstvo-programmista", "Руководство программиста", "33",
        "ГОСТ 19.504-79", "п. 1.2",
        sections=(
            "Назначение и условия применения программ",
            "Характеристика программы",
            "Обращение к программе",
            "Входные и выходные данные",
            "Сообщения",
        ),
        info_part=True,
        aliases=("руководство программиста",),
    ),
    "rukovodstvo-operatora": _dt(
        "rukovodstvo-operatora", "Руководство оператора", "34",
        "ГОСТ 19.505-79", "п. 1.2",
        sections=(
            "Назначение программы",
            "Условия выполнения программы",
            "Выполнение программы",
            "Сообщения оператору",
        ),
        info_part=True,
        aliases=("руководство оператора",),
    ),
    "opisanie-yazyka": _dt(
        "opisanie-yazyka", "Описание языка", "35",
        "ГОСТ 19.506-79", "п. 1.2",
        sections=("Общие сведения", "Элементы языка"),
        info_part=True,
        aliases=("описание языка",),
    ),
    "vedomost-ekspluatatsionnyh-dokumentov": _dt(
        "vedomost-ekspluatatsionnyh-dokumentov",
        "Ведомость эксплуатационных документов", "20",
        "ГОСТ 19.507-79", "п. 3",
        sections=("Документы на программу", "Документы на составные части программы"),
        info_part=False,
        aliases=("ведомость эксплуатационных документов",),
    ),
    # --- ГОСТ 34.201 / ГОСТ Р 59795: документы АС ---
    "rukovodstvo-polzovatelya": _dt(
        "rukovodstvo-polzovatelya", "Руководство пользователя", "И3",
        "ГОСТ Р 59795-2021", "п. 6.4",
        sections=(
            "Введение",
            "Назначение и условия применения",
            "Подготовка к работе",
            "Описание операций",
            "Аварийные ситуации",
            "Рекомендации по освоению",
        ),
        info_part=True,
        aliases=(
            "руководство пользователя",
            "руководство пользователя",
            "описание применения",
        ),
    ),
    "opisanie-po": _dt(
        "opisanie-po", "Описание программного обеспечения", "ПА",
        "ГОСТ Р 59795-2021", "п. 9.1",
        sections=(),
        info_part=True,
        aliases=("описание программного обеспечения", "описание по"),
    ),
}

DEFAULT_TYPE_KEY = "rukovodstvo-polzovatelya"

_ALIAS_INDEX: dict[str, str] = {}
for _key, _dt_obj in DOC_TYPES.items():
    _ALIAS_INDEX[_key] = _key
    _ALIAS_INDEX[_key.replace("-", " ")] = _key
    for _alias in _dt_obj.aliases:
        _ALIAS_INDEX[_alias.strip().lower()] = _key


def _norm(value: str) -> str:
    return " ".join(str(value).strip().lower().replace("_", "-").split())


def resolve(name: str | None) -> DocType:
    """Resolve a document type from a front-matter value.

    Unknown values fall back to :data:`DEFAULT_TYPE_KEY`.
    """
    if not name:
        return DOC_TYPES[DEFAULT_TYPE_KEY]
    key = _ALIAS_INDEX.get(_norm(name)) or _ALIAS_INDEX.get(_norm(name).replace(" ", "-"))
    if key is None:
        return DOC_TYPES[DEFAULT_TYPE_KEY]
    return DOC_TYPES[key]


def missing_sections(doc_type: DocType, headings: list[str]) -> list[str]:
    """Return required sections that are absent from *headings* (case-insensitive)."""
    if not doc_type.sections:
        return []
    norm = [_norm(h) for h in headings]
    missing = []
    for required in doc_type.sections:
        target = _norm(required)
        if not any(target in h or h in target for h in norm if h):
            missing.append(required)
    return missing
