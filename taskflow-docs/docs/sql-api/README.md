# <a id="sql-и-api-для-системного-аналитика">SQL и API для системного аналитика</a>

Единый справочник по 26 файлам: обзор темы, глубокое погружение в SQL и API, сквозной workflow и тесты для самопроверки.

---

## <a id="о-чём-этот-справочник">О чём этот справочник</a>

Это набор учебных и рабочих материалов для системного аналитика. Он покрывает
две ключевые технические компетенции профессии — **SQL** и **API** — а также
показывает, как они связаны в реальной работе.

Материал построен так, чтобы его можно было использовать в четырёх режимах:

1. **Обзор** — быстрый вход через `00-sql-api-overview.md` за 10–15 минут.
2. **Учебник** — последовательное чтение от простого к сложному по трекам.
3. **Справочник** — быстрый поиск нужной темы через указатель или карту связей.
4. **Практика** — самопроверка через `25-quiz.md` (интерактивные тесты).

Все 26 файлов лежат в одном каталоге и ссылаются друг на друга относительными
путями. Это значит, что вы можете открыть любой файл и перейти к связанному
материалу одним кликом — без поиска по папкам.

---

## <a id="для-кого">Для кого</a>

| Роль | Что найдёт |
|---|---|
| **Начинающий аналитик** | Обзор темы → пошаговый путь от SELECT до проектирования API → тесты для проверки |
| **Опытный аналитик** | Глубокие темы: производительность, идемпотентность, безопасность |
| **Тимлид / наставник** | Готовый учебный план с треками, чек-листами и тестами |
| **Разработчик** | Понимание, что аналитик описывает в ТЗ, и как это читать |
| **QA** | Контракты API, edge cases, тестирование интеграций |

---

## <a id="как-читать-справочник">Как читать справочник</a>

**Если вы новичок** — начните с обзора `00-sql-api-overview.md`. Он даст
картину за 15 минут. Затем выберите трек «Junior» в разделе «Учебные треки».

**Если вы готовитесь к собеседованию** — откройте обзор (там шпаргалка и
частые ошибки), чек-листы в конце каждого файла и раздел «Тесты».

**Если вы работаете над задачей** — используйте карту связей (раздел
«Сквозные темы»). Она показывает, какие файлы открыть для конкретной ситуации.

**Если вы хотите проверить знания** — откройте `25-quiz.md` и пройдите тесты.

---

## <a id="структура-каталога">Структура каталога</a>

```
sql-api-analyst/
├── README.md                       ← этот файл
├── 00-sql-api-overview.md          ← обзор всей темы (начните здесь)
│
├── SQL/
│   ├── 01-sql-basics.md
│   ├── 02-sql-joins.md
│   ├── 03-sql-aggregation.md
│   ├── 04-sql-advanced.md
│   ├── 10-sql-ddl-dml.md
│   ├── 11-sql-performance.md
│   ├── 12-sql-dates.md
│   ├── 13-sql-dialects.md
│   └── 14-sql-analytics.md
│
├── API/
│   ├── 05-api-rest.md
│   ├── 06-api-auth.md
│   ├── 07-api-openapi.md
│   ├── 08-api-integrations.md
│   ├── 15-api-http-deep.md
│   ├── 16-api-design-patterns.md
│   ├── 17-api-idempotency.md
│   ├── 18-api-webhooks-deep.md
│   ├── 19-api-messaging.md
│   ├── 20-api-testing.md
│   ├── 21-api-graphql-grpc.md
│   ├── 22-api-caching.md
│   ├── 23-api-monitoring.md
│   └── 24-api-security.md
│
├── Workflow/
│   └── 09-sql-api-workflow.md
│
└── Practice/
    └── 25-quiz.md                  ← тесты для самопроверки
```

---

## <a id="философия-справочника">Философия справочника</a>

Четыре принципа, по которым собран материал.

**Первый — от задачи к инструменту.** Каждый файл начинается с вопроса «зачем
это аналитику», а не с определения.

**Второй — примеры важнее определений.** Везде, где можно показать код или
запрос, он показан.

**Третий — практика в конце.** Каждый файл заканчивается чек-листом и
примерами задач.

**Четвёртый — проверка знаний.** Файл с тестами позволяет объективно оценить,
насколько вы усвоили материал.

---

# <a id="точка-входа">🚪 Точка входа</a>

## <a id="00-sql-api-overview-обзор-всей-темы">[00-sql-api-overview.md](00-sql-api-overview.md) — Обзор всей темы</a>

Прежде чем нырять в глубокие файлы, откройте этот обзор. В нём — сжатая
карта всей темы на 10–15 минут чтения.

**Что внутри:**

| Раздел | О чём |
|---|---|
| 1. Общая логика | Зачем аналитику SQL и API, как они связаны |
| 2. SQL: структура знаний | Уровни владения, ключевые темы, пример запроса, инструменты, чек-лист |
| 3. API: структура знаний | Типы API, REST-основы, аутентификация, OpenAPI, задачи аналитика, паттерны, чек-лист |
| 4. Как SQL и API связаны | Поток данных, пример фичи «Синхронизация заказов», сводная матрица компетенций |
| 5. Порядок изучения | 8 шагов от SELECT до сквозного кейса |
| 6. Частые ошибки | 6 ловушек и как их избежать |
| 7. Шпаргалка | Минимум для работы + инструменты |

**Связанные файлы:**

- Углубление по SQL → [01-sql-basics.md](01-sql-basics.md)
- Углубление по API → [05-api-rest.md](05-api-rest.md)
- Сквозной workflow → [09-sql-api-workflow.md](09-sql-api-workflow.md)
- Проверка знаний → [25-quiz.md](25-quiz.md)

---

# <a id="sql-блок">🗄️ SQL-блок</a>

SQL — рабочий язык аналитика. Даже если вы проектируете API, вам придётся
проверять данные, писать выгрузки для отчётов и согласовывать изменения схемы.
SQL-блок состоит из 9 файлов.

Материал построен по принципу «слоёный пирог»: сначала база, потом связи,
потом агрегаты, потом продвинутые инструменты.

---

## <a id="01-sql-basics-основы-выборки">[01-sql-basics.md](01-sql-basics.md) — Основы выборки</a>

SELECT, WHERE, ORDER BY, LIMIT, DISTINCT, NULL, типы данных, работа со строками и датами.

**Связанные файлы:**
- Углубление по JOIN → [02-sql-joins.md](02-sql-joins.md)
- Работа с датами → [12-sql-dates.md](12-sql-dates.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «SQL: Основы»

## <a id="02-sql-joins-объединение-таблиц">[02-sql-joins.md](02-sql-joins.md) — Объединение таблиц</a>

INNER / LEFT / RIGHT / FULL / CROSS / SELF JOIN, анти-джойн, fan-out, ON vs WHERE.

**Связанные файлы:**
- Основы → [01-sql-basics.md](01-sql-basics.md)
- Производительность JOIN → [11-sql-performance.md](11-sql-performance.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «SQL: JOIN»

## <a id="03-sql-aggregation-агрегация-и-группировка">[03-sql-aggregation.md](03-sql-aggregation.md) — Агрегация и группировка</a>

COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING, WHERE vs HAVING, условная агрегация.

**Связанные файлы:**
- JOIN → [02-sql-joins.md](02-sql-joins.md)
- Статистика и перцентили → [14-sql-analytics.md](14-sql-analytics.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «SQL: Агрегация»

## <a id="04-sql-advanced-продвинутый-sql">[04-sql-advanced.md](04-sql-advanced.md) — Продвинутый SQL</a>

Подзапросы, EXISTS, CTE, оконные функции (ROW_NUMBER, LAG, LEAD, SUM OVER), UNION, CASE.

**Связанные файлы:**
- Агрегация → [03-sql-aggregation.md](03-sql-aggregation.md)
- Аналитика → [14-sql-analytics.md](14-sql-analytics.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «SQL: Продвинутый уровень»

## <a id="10-sql-ddl-dml-ddl-dml-транзакции">[10-sql-ddl-dml.md](10-sql-ddl-dml.md) — DDL, DML, транзакции</a>

CREATE TABLE, ALTER TABLE, INSERT, UPDATE, DELETE, UPSERT, ограничения, транзакции, ACID, VIEW, GRANT.

**Связанные файлы:**
- Ограничения и связи → [02-sql-joins.md](02-sql-joins.md)
- Производительность → [11-sql-performance.md](11-sql-performance.md)

## <a id="11-sql-performance-производительность">[11-sql-performance.md](11-sql-performance.md) — Производительность</a>

Индексы, составные и частичные индексы, EXPLAIN, EXPLAIN ANALYZE, антипаттерны, партиционирование.

**Связанные файлы:**
- DDL и индексы → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- Кэширование на уровне API → [22-api-caching.md](22-api-caching.md)

## <a id="12-sql-dates-даты-время-tz">[12-sql-dates.md](12-sql-dates.md) — Даты, время, TZ</a>

DATE, TIMESTAMP, TIMESTAMPTZ, EXTRACT, DATE_TRUNC, интервалы, AT TIME ZONE, GENERATE_SERIES.

**Связанные файлы:**
- Основы → [01-sql-basics.md](01-sql-basics.md)
- Аналитика временных рядов → [14-sql-analytics.md](14-sql-analytics.md)

## <a id="13-sql-dialects-диалекты-субд">[13-sql-dialects.md](13-sql-dialects.md) — Диалекты СУБД</a>

LIMIT vs TOP vs ROWNUM, строковые функции, даты, COALESCE vs ISNULL vs NVL, UPSERT, JSON.

**Связанные файлы:**
- Основы → [01-sql-basics.md](01-sql-basics.md)
- Даты → [12-sql-dates.md](12-sql-dates.md)

## <a id="14-sql-analytics-аналитика-данных">[14-sql-analytics.md](14-sql-analytics.md) — Аналитика данных</a>

PERCENTILE_CONT, STDDEV, когорты, retention, воронки, RFM, ABC, накопительные метрики.

**Связанные файлы:**
- Агрегация → [03-sql-aggregation.md](03-sql-aggregation.md)
- Оконные функции → [04-sql-advanced.md](04-sql-advanced.md)

---

# <a id="api-блок">🌐 API-блок</a>

API — то, что связывает системы. Аналитик проектирует контракты, описывает
интеграции, следит за надёжностью. API-блок состоит из 14 файлов.

---

## <a id="05-api-rest-rest-основы">[05-api-rest.md](05-api-rest.md) — REST основы</a>

Ресурсы, URL, HTTP-методы, статус-коды, request / response, пагинация, версионирование.

**Связанные файлы:**
- HTTP глубоко → [15-api-http-deep.md](15-api-http-deep.md)
- OpenAPI → [07-api-openapi.md](07-api-openapi.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: REST и HTTP»

## <a id="06-api-auth-аутентификация-и-авторизация">[06-api-auth.md](06-api-auth.md) — Аутентификация и авторизация</a>

API-ключи, Basic, OAuth 2.0, JWT, роли, матрица прав, сценарии 401 и 403.

**Связанные файлы:**
- Безопасность → [24-api-security.md](24-api-security.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Безопасность»

## <a id="07-api-openapi-openapi-swagger">[07-api-openapi.md](07-api-openapi.md) — OpenAPI / Swagger</a>

OpenAPI 3.0, paths, components, schemas, parameters, responses, $ref, Swagger UI.

**Связанные файлы:**
- REST → [05-api-rest.md](05-api-rest.md)
- Тестирование → [20-api-testing.md](20-api-testing.md)

## <a id="08-api-integrations-интеграции">[08-api-integrations.md](08-api-integrations.md) — Интеграции</a>

Синхронные / асинхронные интеграции, webhooks, очереди, пакетный обмен, маппинг, обработка ошибок.

**Связанные файлы:**
- Идемпотентность → [17-api-idempotency.md](17-api-idempotency.md)
- Webhooks глубоко → [18-api-webhooks-deep.md](18-api-webhooks-deep.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Интеграции»

## <a id="15-api-http-deep-http-глубоко">[15-api-http-deep.md](15-api-http-deep.md) — HTTP глубоко</a>

Структура запроса, методы, статус-коды, заголовки, Content Negotiation, CORS, ETag, Cache-Control.

**Связанные файлы:**
- REST → [05-api-rest.md](05-api-rest.md)
- Кэширование → [22-api-caching.md](22-api-caching.md)

## <a id="16-api-design-patterns-паттерны-проектирования">[16-api-design-patterns.md](16-api-design-patterns.md) — Паттерны проектирования</a>

Именование, пагинация, фильтры, формат ошибок, bulk, версионирование, HATEOAS.

**Связанные файлы:**
- REST → [05-api-rest.md](05-api-rest.md)
- OpenAPI → [07-api-openapi.md](07-api-openapi.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Проектирование»

## <a id="17-api-idempotency-идемпотентность-и-надёжность">[17-api-idempotency.md](17-api-idempotency.md) — Идемпотентность и надёжность</a>

Idempotency-Key, retry, backoff, jitter, Circuit Breaker, DLQ, at-most-once / at-least-once / exactly-once.

**Связанные файлы:**
- Интеграции → [08-api-integrations.md](08-api-integrations.md)
- Очереди → [19-api-messaging.md](19-api-messaging.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Идемпотентность»

## <a id="18-api-webhooks-deep-webhooks-глубоко">[18-api-webhooks-deep.md](18-api-webhooks-deep.md) — Webhooks глубоко</a>

События, payload, HMAC, replay protection, retry, идемпотентность, порядок, мониторинг.

**Связанные файлы:**
- Интеграции → [08-api-integrations.md](08-api-integrations.md)
- Идемпотентность → [17-api-idempotency.md](17-api-idempotency.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Интеграции»

## <a id="19-api-messaging-очереди-и-брокеры">[19-api-messaging.md](19-api-messaging.md) — Очереди и брокеры</a>

Kafka, RabbitMQ, SQS / SNS, pub/sub, DLQ, saga, outbox, гарантии доставки.

**Связанные файлы:**
- Интеграции → [08-api-integrations.md](08-api-integrations.md)
- Webhooks → [18-api-webhooks-deep.md](18-api-webhooks-deep.md)

## <a id="20-api-testing-тестирование-api">[20-api-testing.md](20-api-testing.md) — Тестирование API</a>

Postman, Newman, Pact, mock, нагрузочное тестирование, edge cases, SQL-проверка после вызова API.

**Связанные файлы:**
- OpenAPI → [07-api-openapi.md](07-api-openapi.md)
- Идемпотентность → [17-api-idempotency.md](17-api-idempotency.md)

## <a id="21-api-graphql-grpc-graphql-grpc-websocket">[21-api-graphql-grpc.md](21-api-graphql-grpc.md) — GraphQL, gRPC, WebSocket</a>

GraphQL schema, .proto, gRPC streaming, WebSocket protocol, SSE, сравнение подходов.

**Связанные файлы:**
- REST → [05-api-rest.md](05-api-rest.md)
- HTTP → [15-api-http-deep.md](15-api-http-deep.md)

## <a id="22-api-caching-кэширование">[22-api-caching.md](22-api-caching.md) — Кэширование</a>

Cache-Control, ETag, If-None-Match, Redis, TTL, инвалидация, stampede, penetration, avalanche.

**Связанные файлы:**
- HTTP → [15-api-http-deep.md](15-api-http-deep.md)
- Производительность SQL → [11-sql-performance.md](11-sql-performance.md)

## <a id="23-api-monitoring-мониторинг">[23-api-monitoring.md](23-api-monitoring.md) — Мониторинг</a>

Logs, metrics, traces, RED, SLI / SLO / SLA, error budget, алерты, дашборды.

**Связанные файлы:**
- Кэширование → [22-api-caching.md](22-api-caching.md)
- Безопасность → [24-api-security.md](24-api-security.md)

## <a id="24-api-security-безопасность">[24-api-security.md](24-api-security.md) — Безопасность</a>

OWASP API Top 10, BOLA / IDOR, RBAC / ABAC, маскирование PII, rate limiting, аудит, whitelist полей.

**Связанные файлы:**
- Auth → [06-api-auth.md](06-api-auth.md)
- HTTP → [15-api-http-deep.md](15-api-http-deep.md)
- Тесты → [25-quiz.md](25-quiz.md), раздел «API: Безопасность»

---

# 🔄 Workflow

## <a id="09-sql-api-workflow-сквозной-процесс">[09-sql-api-workflow.md](09-sql-api-workflow.md) — Сквозной процесс</a>

Как связаны SQL и API, типовой workflow аналитика, сквозной кейс
«Синхронизация заказов», шаблоны документов, чек-листы.

**Связанные файлы:**
- Обзор → [00-sql-api-overview.md](00-sql-api-overview.md)
- Интеграции → [08-api-integrations.md](08-api-integrations.md)
- Идемпотентность → [17-api-idempotency.md](17-api-idempotency.md)

---

# <a id="практика">🧪 Практика</a>

## <a id="25-quiz-тесты-для-самопроверки">[25-quiz.md](25-quiz.md) — Тесты для самопроверки</a>

25 интерактивных вопросов по всем ключевым темам справочника. Написаны на
Markdown с использованием плагина `mkdocs-quiz`.

**Что внутри:**

| Раздел | Кол-во вопросов |
|---|---|
| SQL: Основы | 4 |
| SQL: JOIN | 3 |
| SQL: Агрегация | 3 |
| SQL: Продвинутый уровень | 3 |
| API: REST и HTTP | 4 |
| API: Проектирование | 3 |
| API: Идемпотентность | 3 |
| API: Интеграции | 3 |
| API: Безопасность | 2 |

**Типы вопросов:**

- одиночный выбор;
- множественный выбор;
- заполнение пропуска (через `[[ответ]]`);
- блок пояснения после ответа.

**Как использовать:**

1. **В терминале** — если установлен `mkdocs-quiz`:
   ```bash
   mkdocs-quiz run 25-quiz.md
   ```
2. **В браузере** — если используете MkDocs для документации:
   ```bash
   pip install mkdocs-quiz
   mkdocs serve
   ```
3. **Статически** — откройте файл в редакторе Markdown с поддержкой
   сворачиваемых блоков (`<details>`).

**Связанные файлы:**

- Все разделы SQL-блока → [01–04](01-sql-basics.md), [10–14](10-sql-ddl-dml.md)
- Все разделы API-блока → [05–08](05-api-rest.md), [15–24](15-api-http-deep.md)
- Сквозной workflow → [09-sql-api-workflow.md](09-sql-api-workflow.md)

---

# <a id="сквозные-темы-карта-связей">🗺️ Сквозные темы (карта связей)</a>

Маршруты по файлам для типовых рабочих ситуаций.

## <a id="тема-синхронизация-данных-между-системами">Тема: «Синхронизация данных между системами»</a>

**Сначала:** [00-sql-api-overview.md](00-sql-api-overview.md), раздел 4.

1. [08-api-integrations.md](08-api-integrations.md) — общая картина
2. [17-api-idempotency.md](17-api-idempotency.md) — защита от дублей
3. [18-api-webhooks-deep.md](18-api-webhooks-deep.md) — push-уведомления
4. [19-api-messaging.md](19-api-messaging.md) — очереди
5. [10-sql-ddl-dml.md](10-sql-ddl-dml.md) — UPSERT
6. [23-api-monitoring.md](23-api-monitoring.md) — наблюдаемость
7. [25-quiz.md](25-quiz.md) — проверка по разделу «API: Интеграции»

## <a id="тема-проектирование-нового-api">Тема: «Проектирование нового API»</a>

**Сначала:** [00-sql-api-overview.md](00-sql-api-overview.md), раздел 3.

1. [05-api-rest.md](05-api-rest.md) — основы
2. [16-api-design-patterns.md](16-api-design-patterns.md) — паттерны
3. [06-api-auth.md](06-api-auth.md) — авторизация
4. [24-api-security.md](24-api-security.md) — защита
5. [07-api-openapi.md](07-api-openapi.md) — спецификация
6. [20-api-testing.md](20-api-testing.md) — проверка
7. [25-quiz.md](25-quiz.md) — проверка по разделам «API: REST и HTTP», «API: Проектирование», «API: Безопасность»

## <a id="тема-анализ-данных-и-метрики">Тема: «Анализ данных и метрики»</a>

**Сначала:** [00-sql-api-overview.md](00-sql-api-overview.md), раздел 2.

1. [01-sql-basics.md](01-sql-basics.md) — база
2. [02-sql-joins.md](02-sql-joins.md) — соединения
3. [03-sql-aggregation.md](03-sql-aggregation.md) — агрегаты
4. [04-sql-advanced.md](04-sql-advanced.md) — окна и CTE
5. [12-sql-dates.md](12-sql-dates.md) — временные ряды
6. [14-sql-analytics.md](14-sql-analytics.md) — retention, RFM, воронки
7. [25-quiz.md](25-quiz.md) — проверка по разделам «SQL: *»

## <a id="тема-производительность">Тема: «Производительность»</a>

1. [11-sql-performance.md](11-sql-performance.md) — индексы, EXPLAIN
2. [22-api-caching.md](22-api-caching.md) — кэш
3. [23-api-monitoring.md](23-api-monitoring.md) — метрики и алерты
4. [16-api-design-patterns.md](16-api-design-patterns.md) — пагинация

## <a id="тема-работа-с-ошибками">Тема: «Работа с ошибками»</a>

1. [15-api-http-deep.md](15-api-http-deep.md) — статус-коды
2. [16-api-design-patterns.md](16-api-design-patterns.md) — формат ошибок
3. [17-api-idempotency.md](17-api-idempotency.md) — retry, DLQ
4. [18-api-webhooks-deep.md](18-api-webhooks-deep.md) — retry webhooks
5. [23-api-monitoring.md](23-api-monitoring.md) — алерты
6. [25-quiz.md](25-quiz.md) — проверка по разделу «API: Идемпотентность»

## <a id="тема-безопасность">Тема: «Безопасность»</a>

1. [24-api-security.md](24-api-security.md) — OWASP, атаки
2. [06-api-auth.md](06-api-auth.md) — токены
3. [15-api-http-deep.md](15-api-http-deep.md) — CORS, заголовки
4. [10-sql-ddl-dml.md](10-sql-ddl-dml.md) — права доступа
5. [25-quiz.md](25-quiz.md) — проверка по разделу «API: Безопасность»

---

# <a id="учебные-треки">🎓 Учебные треки</a>

Три трека, рассчитанные на разные уровни. Каждый трек начинается с обзора,
заканчивается тестами.

## <a id="трек-junior-системный-аналитик-4-недели">Трек «Junior системный аналитик» (4 недели)</a>

**Неделя 0 — вводная:** [00-sql-api-overview.md](00-sql-api-overview.md)

**Далее:**

1. [01-sql-basics.md](01-sql-basics.md) — неделя 1
2. [02-sql-joins.md](02-sql-joins.md) — неделя 1
3. [03-sql-aggregation.md](03-sql-aggregation.md) — неделя 2
4. [05-api-rest.md](05-api-rest.md) — неделя 2
5. [06-api-auth.md](06-api-auth.md) — неделя 3
6. [09-sql-api-workflow.md](09-sql-api-workflow.md) — неделя 4
7. [25-quiz.md](25-quiz.md) — проверка (разделы SQL: Основы, JOIN, Агрегация; API: REST и HTTP)

**Результат:** пишете запросы средней сложности, понимаете контракты API,
знаете, как описать простую интеграцию.

## <a id="трек-middle-системный-аналитик-8-недель">Трек «Middle системный аналитик» (8 недель)</a>

**Начните с:** [00-sql-api-overview.md](00-sql-api-overview.md)

**Всё из junior, плюс:**

7. [04-sql-advanced.md](04-sql-advanced.md) — неделя 3
8. [10-sql-ddl-dml.md](10-sql-ddl-dml.md) — неделя 4
9. [11-sql-performance.md](11-sql-performance.md) — неделя 4
10. [12-sql-dates.md](12-sql-dates.md) — неделя 5
11. [07-api-openapi.md](07-api-openapi.md) — неделя 5
12. [08-api-integrations.md](08-api-integrations.md) — неделя 6
13. [15-api-http-deep.md](15-api-http-deep.md) — неделя 6
14. [16-api-design-patterns.md](16-api-design-patterns.md) — неделя 7
15. [17-api-idempotency.md](17-api-idempotency.md) — неделя 8
16. [25-quiz.md](25-quiz.md) — проверка (все разделы)

**Результат:** проектируете API, описываете интеграции, диагностируете
проблемы с данными.

## <a id="трек-senior-системный-аналитик-12-недель">Трек «Senior системный аналитик» (12 недель)</a>

**Начните с:** [00-sql-api-overview.md](00-sql-api-overview.md)

**Всё из middle, плюс:**

17. [13-sql-dialects.md](13-sql-dialects.md) — неделя 8
18. [14-sql-analytics.md](14-sql-analytics.md) — неделя 9
19. [18-api-webhooks-deep.md](18-api-webhooks-deep.md) — неделя 9
20. [19-api-messaging.md](19-api-messaging.md) — неделя 10
21. [20-api-testing.md](20-api-testing.md) — неделя 10
22. [21-api-graphql-grpc.md](21-api-graphql-grpc.md) — неделя 11
23. [22-api-caching.md](22-api-caching.md) — неделя 11
24. [23-api-monitoring.md](23-api-monitoring.md) — неделя 12
25. [24-api-security.md](24-api-security.md) — неделя 12
26. [25-quiz.md](25-quiz.md) — итоговая проверка

**Результат:** ведёте сложные интеграции, проектируете отказоустойчивые
системы, говорите с разработчиками и безопасниками на одном языке.

---

# <a id="предметный-указатель">🔍 Предметный указатель</a>

### 0
- **Обзор темы** → [00-sql-api-overview.md](00-sql-api-overview.md)

### A
- **ACID** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **API-ключи** → [06-api-auth.md](06-api-auth.md)
- **AVG** → [03-sql-aggregation.md](03-sql-aggregation.md)

### B
- **Backoff** → [17-api-idempotency.md](17-api-idempotency.md)
- **BPMN** → [09-sql-api-workflow.md](09-sql-api-workflow.md)
- **BOLA** → [24-api-security.md](24-api-security.md)

### C
- **Cache-Control** → [22-api-caching.md](22-api-caching.md)
- **CASE** → [04-sql-advanced.md](04-sql-advanced.md)
- **CORS** → [15-api-http-deep.md](15-api-http-deep.md)
- **COUNT** → [03-sql-aggregation.md](03-sql-aggregation.md)
- **CTE** → [04-sql-advanced.md](04-sql-advanced.md)

### D
- **DATE_TRUNC** → [12-sql-dates.md](12-sql-dates.md)
- **DDL** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **DELETE** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **DLQ** → [17-api-idempotency.md](17-api-idempotency.md), [19-api-messaging.md](19-api-messaging.md)
- **DML** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

### E
- **ETag** → [15-api-http-deep.md](15-api-http-deep.md), [22-api-caching.md](22-api-caching.md)
- **EXPLAIN** → [11-sql-performance.md](11-sql-performance.md)
- **EXISTS** → [04-sql-advanced.md](04-sql-advanced.md)

### G
- **GraphQL** → [21-api-graphql-grpc.md](21-api-graphql-grpc.md)
- **GROUP BY** → [03-sql-aggregation.md](03-sql-aggregation.md)
- **gRPC** → [21-api-graphql-grpc.md](21-api-graphql-grpc.md)

### H
- **HATEOAS** → [16-api-design-patterns.md](16-api-design-patterns.md)
- **HAVING** → [03-sql-aggregation.md](03-sql-aggregation.md)
- **HMAC** → [18-api-webhooks-deep.md](18-api-webhooks-deep.md)
- **HTTP** → [15-api-http-deep.md](15-api-http-deep.md)

### I
- **Idempotency-Key** → [17-api-idempotency.md](17-api-idempotency.md)
- **INDEX** → [11-sql-performance.md](11-sql-performance.md)
- **INSERT** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

### J
- **JOIN** → [02-sql-joins.md](02-sql-joins.md)
- **JWT** → [06-api-auth.md](06-api-auth.md)

### K
- **Kafka** → [19-api-messaging.md](19-api-messaging.md)

### L
- **LAG / LEAD** → [04-sql-advanced.md](04-sql-advanced.md)
- **LEFT JOIN** → [02-sql-joins.md](02-sql-joins.md)
- **LIMIT** → [01-sql-basics.md](01-sql-basics.md)

### M
- **MATERIALIZED VIEW** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **MERGE / UPSERT** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **Monitoring** → [23-api-monitoring.md](23-api-monitoring.md)

### O
- **OAuth 2.0** → [06-api-auth.md](06-api-auth.md)
- **OpenAPI** → [07-api-openapi.md](07-api-openapi.md)
- **OWASP API Top 10** → [24-api-security.md](24-api-security.md)

### P
- **Pagination** → [16-api-design-patterns.md](16-api-design-patterns.md)
- **PERCENTILE_CONT** → [14-sql-analytics.md](14-sql-analytics.md)
- **Postman** → [20-api-testing.md](20-api-testing.md)
- **PRIMARY KEY** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **PUT vs PATCH** → [15-api-http-deep.md](15-api-http-deep.md)

### Q
- **Quiz** → [25-quiz.md](25-quiz.md)

### R
- **RabbitMQ** → [19-api-messaging.md](19-api-messaging.md)
- **Rate limiting** → [24-api-security.md](24-api-security.md)
- **Retention (SQL)** → [14-sql-analytics.md](14-sql-analytics.md)
- **Retry** → [17-api-idempotency.md](17-api-idempotency.md)
- **RFM** → [14-sql-analytics.md](14-sql-analytics.md)
- **ROW_NUMBER** → [04-sql-advanced.md](04-sql-advanced.md)

### S
- **SELECT** → [01-sql-basics.md](01-sql-basics.md)
- **SLI / SLO / SLA** → [23-api-monitoring.md](23-api-monitoring.md)
- **SSE** → [21-api-graphql-grpc.md](21-api-graphql-grpc.md)
- **SSRF** → [24-api-security.md](24-api-security.md)
- **Swagger** → [07-api-openapi.md](07-api-openapi.md)

### T
- **TIMESTAMPTZ** → [12-sql-dates.md](12-sql-dates.md)
- **Transactions** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

### U
- **UNION** → [04-sql-advanced.md](04-sql-advanced.md)
- **UPDATE** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)
- **UPSERT** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

### V
- **VIEW** → [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

### W
- **Webhook** → [18-api-webhooks-deep.md](18-api-webhooks-deep.md)
- **WebSocket** → [21-api-graphql-grpc.md](21-api-graphql-grpc.md)
- **WHERE** → [01-sql-basics.md](01-sql-basics.md)
- **WINDOW FUNCTIONS** → [04-sql-advanced.md](04-sql-advanced.md)

---

# <a id="матрица-покрытия-навыков">📊 Матрица покрытия навыков</a>

| Навык | Файлы |
|---|---|
| **Обзор темы** | [00](00-sql-api-overview.md) |
| Написание SELECT | [01](01-sql-basics.md), [02](02-sql-joins.md), [03](03-sql-aggregation.md) |
| Сложные запросы | [04](04-sql-advanced.md), [14](14-sql-analytics.md) |
| Работа с данными | [10](10-sql-ddl-dml.md) |
| Оптимизация | [11](11-sql-performance.md) |
| Работа с датами | [12](12-sql-dates.md) |
| Переносимость SQL | [13](13-sql-dialects.md) |
| Проектирование REST | [05](05-api-rest.md), [16](16-api-design-patterns.md) |
| Аутентификация | [06](06-api-auth.md) |
| Документирование | [07](07-api-openapi.md) |
| Интеграции | [08](08-api-integrations.md), [17](17-api-idempotency.md), [19](19-api-messaging.md) |
| Webhooks | [18](18-api-webhooks-deep.md) |
| Тестирование | [20](20-api-testing.md) |
| GraphQL / gRPC | [21](21-api-graphql-grpc.md) |
| Кэширование | [22](22-api-caching.md) |
| Мониторинг | [23](23-api-monitoring.md) |
| Безопасность | [24](24-api-security.md) |
| Сквозной workflow | [09](09-sql-api-workflow.md) |
| **Самопроверка** | [25](25-quiz.md) |

---

# <a id="как-пользоваться-справочником">✅ Как пользоваться справочником</a>

**Если учитесь с нуля:**

1. Прочитайте [00-sql-api-overview.md](00-sql-api-overview.md) — 10–15 минут.
2. Выберите трек в разделе «Учебные треки».
3. Двигайтесь по файлам последовательно.
4. После каждого файла выполняйте практические задачи.
5. Каждые 2–3 файла проходите соответствующий раздел [25-quiz.md](25-quiz.md).

**Если готовитесь к собеседованию:**

1. Прочитайте [00-sql-api-overview.md](00-sql-api-overview.md) — там шпаргалка.
2. Пройдите все тесты в [25-quiz.md](25-quiz.md).
3. Откройте чек-листы в конце каждого файла.
4. Разберите сквозной кейс в [09-sql-api-workflow.md](09-sql-api-workflow.md).

**Если решаете рабочую задачу:**

1. Найдите ситуацию в «Сквозных темах».
2. Начните с обзора — раздел 4 «Как SQL и API связаны».
3. Откройте глубокие файлы по маршруту.
4. Используйте шаблоны из [09-sql-api-workflow.md](09-sql-api-workflow.md).

**Если хотите проверить знания:**

1. Откройте [25-quiz.md](25-quiz.md).
2. Пройдите тесты — прогресс сохраняется в браузере.
3. Для слабых тем вернитесь к соответствующим файлам.

---

# <a id="соглашения">📝 Соглашения</a>

- **Обзорный файл** — `00-sql-api-overview.md` — сжат в одну страницу.
- **Файл тестов** — `25-quiz.md` — использует синтаксис `mkdocs-quiz`.
- Примеры SQL — в синтаксисе PostgreSQL, если не указано иное.
- Примеры API — REST + JSON.
- Ссылки между файлами — относительные, работают в одном каталоге.

---

# <a id="внешние-ресурсы">🔗 Внешние ресурсы</a>

- **PostgreSQL docs** — https://www.postgresql.org/docs/
- **OpenAPI spec** — https://spec.openapis.org/oas/latest.html
- **OWASP API Security** — https://owasp.org/www-project-api-security/
- **MDN HTTP** — https://developer.mozilla.org/ru/docs/Web/HTTP
- **Kafka docs** — https://kafka.apache.org/documentation/
- **Postman Learning Center** — https://learning.postman.com/
- **mkdocs-quiz** — https://github.com/lekrans/mkdocs-quiz

---

# <a id="что-дальше">🚧 Что дальше</a>

Справочник развивается. В планах:

- Добавить **workflow-блок** (требования, BPMN, UML, user story, приоритизация).
- Расширить **SQL-блок** разделом про миграции и версионирование схемы.
- Добавить **примеры реальных ТЗ** по интеграциям.
- Расширить **тесты** — вопросы по Kafka, кэшированию, мониторингу, GraphQL.
- Сделать **чек-лист для собеседования** системного аналитика.

---

*Последнее обновление: 2026-10-14*
