# <a id="тесты-по-sql-и-api">🧪 Тесты по SQL и API</a>

> **Как проходить:** выберите ответ и нажмите «Проверить».
> Прогресс сохраняется в браузере.
>
> **Охват:** все 24 учебных файла справочника. ~140 вопросов.

<!-- mkdocs-quiz intro -->

---

## <a id="sql-основы">SQL: Основы</a>

📖 **Перечитать:** [01-sql-basics.md](01-sql-basics.md)

<quiz>
Что вернёт запрос `SELECT name FROM users WHERE age > 18`?

- [ ] Все имена пользователей
- [x] Имена пользователей старше 18 лет
- [ ] Имена пользователей младше 18 лет
- [ ] Ошибку

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 3 «WHERE — фильтрация»](01-sql-basics.md#3-where-фильтрация)
</quiz>

<quiz>
Какой оператор используется для сортировки результатов?

- [ ] `GROUP BY`
- [x] `ORDER BY`
- [ ] `SORT BY`
- [ ] `ARRANGE BY`

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 4 «ORDER BY»](01-sql-basics.md#4-order-by-сортировка)
</quiz>

<quiz>
Что вернёт выражение `NULL = NULL`?

- [ ] `TRUE`
- [ ] `FALSE`
- [x] `NULL`
- [ ] Ошибку

В SQL трёхзначная логика. Для проверки на NULL используют `IS NULL`.

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 5 «NULL — главная ловушка»](01-sql-basics.md#основные-операторы)
</quiz>

<quiz>
Какой оператор SQL используется для фильтрации строк?

- [ ] `ORDER BY`
- [x] `WHERE`
- [ ] `GROUP BY`
- [ ] `LIMIT`

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 3 «WHERE — фильтрация»](01-sql-basics.md#3-where-фильтрация)
</quiz>

<quiz>
Чем `DISTINCT` отличается от `GROUP BY`?

- [ ] Ничем
- [x] `DISTINCT` убирает дубли, `GROUP BY` группирует для агрегатов
- [ ] `DISTINCT` быстрее
- [ ] `GROUP BY` работает только с числами

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 6 «DISTINCT»](01-sql-basics.md#6-distinct-уникальные-значения)
</quiz>

<quiz>
Какой оператор используется для поиска по шаблону?

- [ ] `MATCH`
- [x] `LIKE`
- [ ] `SEARCH`
- [ ] `FIND`

`%` — любое количество символов, `_` — один символ.

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 3.1 «Основные операторы»](01-sql-basics.md#основные-операторы)
</quiz>

<quiz>
Что вернёт `COALESCE(phone, 'не указан')`?

- [ ] Всегда `phone`
- [x] Значение `phone`, если оно не NULL, иначе `'не указан'`
- [ ] Всегда `'не указан'`
- [ ] Ошибку, если `phone` = NULL

📖 [01-sql-basics.md](01-sql-basics.md) → [раздел 5 «COALESCE и NULLIF»](01-sql-basics.md#coalesce-и-nullif)
</quiz>

<quiz>
Какой оператор ограничивает выборку в MS SQL?

- [ ] `LIMIT`
- [x] `TOP`
- [ ] `FETCH`
- [ ] `ROWNUM`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 3 «Ограничение строк»](13-sql-dialects.md#3-ограничение-строк)
</quiz>

---

## SQL: JOIN

📖 **Перечитать:** [02-sql-joins.md](02-sql-joins.md)

<quiz>
Какой JOIN вернёт всех пользователей, включая тех, у кого нет заказов?

- [ ] `INNER JOIN`
- [x] `LEFT JOIN`
- [ ] `RIGHT JOIN`
- [ ] `FULL JOIN`

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 5 «LEFT JOIN»](02-sql-joins.md#4-left-join)
</quiz>

<quiz>
Как найти пользователей без заказов?

- [x] `SELECT u.id FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE o.id IS NULL;`
- [ ] `SELECT u.id FROM users u JOIN orders o ON u.id = o.user_id;`
- [ ] `SELECT u.id FROM users WHERE id NOT IN (SELECT user_id FROM orders);`
- [ ] `SELECT u.id FROM users CROSS JOIN orders;`

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 5.1 «Анти-джойн»](02-sql-joins.md#4-left-join)
</quiz>

<quiz>
Что произойдёт, если в `LEFT JOIN` добавить условие по правой таблице в `WHERE`?

- [ ] Ничего не изменится
- [x] `LEFT JOIN` превратится в `INNER JOIN`
- [ ] Запрос вернёт ошибку
- [ ] Появятся дубли

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 9 «ON vs WHERE»](02-sql-joins.md#10-типичные-ошибки)
</quiz>

<quiz>
Что такое fan-out при JOIN?

- [ ] Потеря строк
- [x] Размножение строк из-за связи один-ко-многим
- [ ] Ошибка синтаксиса
- [ ] Ускорение запроса

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 10 «Ловушка: размножение строк»](02-sql-joins.md#пример-ловушки-с-дублями)
</quiz>

<quiz>
Какой JOIN оставит только совпадающие строки из двух таблиц?

- [ ] `LEFT JOIN`
- [x] `INNER JOIN`
- [ ] `FULL JOIN`
- [ ] `CROSS JOIN`

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 3 «INNER JOIN»](02-sql-joins.md#3-inner-join)
</quiz>

<quiz>
Какой JOIN вернёт все строки из обеих таблиц, включая несовпадающие?

- [ ] `INNER JOIN`
- [ ] `LEFT JOIN`
- [ ] `RIGHT JOIN`
- [x] `FULL JOIN`

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 7 «FULL JOIN»](02-sql-joins.md#6-full-join)
</quiz>

<quiz>
Как соединить таблицу саму с собой?

- [ ] `CROSS JOIN`
- [x] `SELF JOIN`
- [ ] `OUTER JOIN`
- [ ] `NATURAL JOIN`

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 11 «SELF JOIN»](02-sql-joins.md#8-self-join)
</quiz>

<quiz>
Что вернёт `CROSS JOIN` двух таблиц с 5 и 3 строками?

- [ ] 3 строки
- [ ] 5 строк
- [x] 15 строк
- [ ] 8 строк

Декартово произведение: 5 × 3 = 15.

📖 [02-sql-joins.md](02-sql-joins.md) → [раздел 7 «CROSS JOIN»](02-sql-joins.md#7-cross-join)
</quiz>

---

## <a id="sql-агрегация">SQL: Агрегация</a>

📖 **Перечитать:** [03-sql-aggregation.md](03-sql-aggregation.md)

<quiz>
Чем `COUNT(*)` отличается от `COUNT(email)`?

- [ ] Ничем
- [x] `COUNT(*)` считает все строки, `COUNT(email)` — только непустые email
- [ ] `COUNT(*)` считает уникальные строки
- [ ] `COUNT(email)` работает быстрее

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 2 «COUNT(*) vs COUNT(col)»](03-sql-aggregation.md#1-агрегатные-функции)
</quiz>

<quiz>
Где можно фильтровать по агрегату (`SUM`, `AVG`)?

- [ ] В `WHERE`
- [x] В `HAVING`
- [ ] В `ORDER BY`
- [ ] В `GROUP BY`

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 5 «HAVING vs WHERE»](03-sql-aggregation.md#where-vs-having)
</quiz>

<quiz>
Что вернёт `SELECT status, COUNT(*) FROM orders GROUP BY status;`?

- [ ] Одну строку
- [x] По одной строке на каждый уникальный статус
- [ ] Ошибку
- [ ] Все заказы

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 3 «GROUP BY»](03-sql-aggregation.md#2-group-by)
</quiz>

<quiz>
Какая агрегатная функция подсчитывает количество строк?

- [ ] `SUM`
- [x] `COUNT`
- [ ] `AVG`
- [ ] `MAX`

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 1 «Агрегатные функции»](03-sql-aggregation.md#1-агрегатные-функции)
</quiz>

<quiz>
Какая функция вернёт количество уникальных значений?

- [ ] `COUNT(col)`
- [x] `COUNT(DISTINCT col)`
- [ ] `UNIQUE(col)`
- [ ] `DISTINCT(col)`

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 2 «COUNT(*) vs COUNT(col)»](03-sql-aggregation.md#1-агрегатные-функции)
</quiz>

<quiz>
Что вернёт `SELECT AVG(amount) FROM orders`?

- [ ] Сумму
- [x] Среднее значение `amount`
- [ ] Количество
- [ ] Минимум

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 1 «Агрегатные функции»](03-sql-aggregation.md#1-агрегатные-функции)
</quiz>

<quiz>
Зачем нужна условная агрегация через `CASE` внутри `SUM`?

- [ ] Для сортировки
- [x] Чтобы посчитать несколько метрик в одном запросе
- [ ] Для фильтрации строк
- [ ] Для ускорения запроса

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 8 «Условная агрегация»](03-sql-aggregation.md#условная-агрегация)
</quiz>

<quiz>
Какое ключевое слово в SQL используется для группировки строк по значению поля?

- [ ] `ORDER BY`
- [x] `GROUP BY`
- [ ] `HAVING`
- [ ] `DISTINCT`

📖 [03-sql-aggregation.md](03-sql-aggregation.md) → [раздел 3 «GROUP BY»](03-sql-aggregation.md#2-group-by)
</quiz>

---

## <a id="sql-продвинутый">SQL: Продвинутый</a>

📖 **Перечитать:** [04-sql-advanced.md](04-sql-advanced.md)

<quiz>
Для чего используется `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)`?

- [ ] Для сортировки заказов
- [x] Для нумерации заказов внутри каждого пользователя
- [ ] Для подсчёта общего количества заказов
- [ ] Для группировки по пользователю

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 3 «ROW_NUMBER»](04-sql-advanced.md#row-number-нумерация)
</quiz>

<quiz>
Что делает `LAG(amount) OVER (ORDER BY created_at)`?

- [ ] Возвращает сумму amount
- [x] Возвращает значение amount из предыдущей строки
- [ ] Возвращает первую строку
- [ ] Возвращает последнюю строку

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 3.4 «LAG / LEAD»](04-sql-advanced.md#lag-lead-соседние-строки)
</quiz>

<quiz>
Какая оконная функция нумерует строки внутри группы?

- [ ] `RANK`
- [x] `ROW_NUMBER`
- [ ] `LAG`
- [ ] `LEAD`

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 3.2 «ROW_NUMBER — нумерация»](04-sql-advanced.md#row-number-нумерация)
</quiz>

<quiz>
Чем `ROW_NUMBER()` отличается от `RANK()`?

- [ ] Ничем
- [x] `ROW_NUMBER` даёт уникальные номера, `RANK` — с пропусками при равенстве
- [ ] `RANK` работает только с числами
- [ ] `ROW_NUMBER` медленнее

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 3.3 «RANK / DENSE_RANK»](04-sql-advanced.md#rank-dense-rank)
</quiz>

<quiz>
Что такое CTE?

- [ ] Хранимая процедура
- [x] Именованный временный результирующий набор через `WITH`
- [ ] Индекс
- [ ] Триггер

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 2 «CTE (WITH)»](04-sql-advanced.md#2-cte-with)
</quiz>

<quiz>
Чем `UNION` отличается от `UNION ALL`?

- [ ] Ничем
- [x] `UNION` удаляет дубли, `UNION ALL` — нет
- [ ] `UNION ALL` работает только с числами
- [ ] `UNION` быстрее

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 4 «UNION / UNION ALL»](04-sql-advanced.md#4-union-union-all)
</quiz>

<quiz>
Что вернёт `SUM(amount) OVER (ORDER BY created_at)`?

- [ ] Общую сумму
- [x] Накопительную сумму по порядку даты
- [ ] Первое значение
- [ ] Последнее значение

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 3.4 «SUM / AVG OVER»](04-sql-advanced.md#sum-avg-over)
</quiz>

<quiz>
Какой оператор проверяет, что подзапрос возвращает хотя бы одну строку?

- [ ] `IN`
- [x] `EXISTS`
- [ ] `ANY`
- [ ] `ALL`

📖 [04-sql-advanced.md](04-sql-advanced.md) → [раздел 1.3 «EXISTS / NOT EXISTS»](04-sql-advanced.md#exists-not-exists)
</quiz>

---

## <a id="sql-ddl-dml-транзакции">SQL: DDL / DML / Транзакции</a>

📖 **Перечитать:** [10-sql-ddl-dml.md](10-sql-ddl-dml.md)

<quiz>
Какое ограничение гарантирует уникальность значения в колонке?

- [ ] `PRIMARY KEY`
- [x] `UNIQUE`
- [ ] `CHECK`
- [ ] `DEFAULT`

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 4 «Ограничения целостности»](10-sql-ddl-dml.md#4-ограничения-целостности)
</quiz>

<quiz>
Что делает `ON DELETE CASCADE`?

- [ ] Запрещает удаление
- [x] Каскадно удаляет связанные строки
- [ ] Устанавливает NULL
- [ ] Логирует удаление

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 4 «Поведение при удалении родителя»](10-sql-ddl-dml.md#поведение-при-удалении-родителя)
</quiz>

<quiz>
Что означает ACID?

- [x] Atomicity, Consistency, Isolation, Durability
- [ ] Access, Control, Integrity, Data
- [ ] Atomic, Commit, Insert, Delete
- [ ] Альтернативный способ транзакций

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 5 «Транзакции и ACID»](10-sql-ddl-dml.md#5-транзакции-и-acid)
</quiz>

<quiz>
Какой синтаксис используется в PostgreSQL для идемпотентной вставки?

- [ ] `ON DUPLICATE KEY UPDATE`
- [x] `ON CONFLICT`
- [ ] `MERGE`
- [ ] `UPSERT`

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 3 «UPSERT»](10-sql-ddl-dml.md#upsert-insert-on-conflict)
</quiz>

<quiz>
Что произойдёт, если выполнить `UPDATE users SET status = 'blocked'` без `WHERE`?

- [ ] Ошибка
- [ ] Ничего
- [x] Обновятся все строки таблицы
- [ ] Обновится первая строка

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 3 «UPDATE»](10-sql-ddl-dml.md#update)
</quiz>

<quiz>
Зачем нужен `ROLLBACK`?

- [ ] Зафиксировать изменения
- [x] Откатить транзакцию
- [ ] Удалить таблицу
- [ ] Создать индекс

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 5 «Транзакции и ACID»](10-sql-ddl-dml.md#5-транзакции-и-acid)
</quiz>

<quiz>
Что такое `MATERIALIZED VIEW`?

- [ ] Виртуальная таблица
- [x] Физически сохранённый результат запроса, требующий `REFRESH`
- [ ] Индекс
- [ ] Триггер

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 6 «MATERIALIZED VIEW»](10-sql-ddl-dml.md#6-view-и-materialized-view)
</quiz>

<quiz>
Какое ограничение задаёт связь между таблицами?

- [ ] `UNIQUE`
- [x] `FOREIGN KEY`
- [ ] `CHECK`
- [ ] `NOT NULL`

📖 [10-sql-ddl-dml.md](10-sql-ddl-dml.md) → [раздел 4 «Ограничения целостности»](10-sql-ddl-dml.md#4-ограничения-целостности)
</quiz>

---

## <a id="sql-производительность">SQL: Производительность</a>

📖 **Перечитать:** [11-sql-performance.md](11-sql-performance.md)

<quiz>
Зачем нужны индексы?

- [ ] Для хранения данных
- [x] Для ускорения поиска и JOIN
- [ ] Для сжатия данных
- [ ] Для шифрования

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 3 «Индексы»](11-sql-performance.md#3-индексы)
</quiz>

<quiz>
Что показывает `EXPLAIN ANALYZE`?

- [ ] Схему таблицы
- [x] План выполнения запроса и реальное время
- [ ] Список индексов
- [ ] Права доступа

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 4 «EXPLAIN ANALYZE»](11-sql-performance.md#explain-analyze)
</quiz>

<quiz>
Что плохого в `WHERE YEAR(created_at) = 2026`?

- [ ] Синтаксическая ошибка
- [x] Функция на поле мешает использованию индекса
- [ ] Возвращает неверный результат
- [ ] Работает только с MS SQL

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 5 «Антипаттерны»](11-sql-performance.md#5-антипаттерны)
</quiz>

<quiz>
Какая команда показывает план запроса без его выполнения?

- [ ] `ANALYZE`
- [x] `EXPLAIN`
- [ ] `SHOW PLAN`
- [ ] `DESCRIBE`

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 4 «EXPLAIN»](11-sql-performance.md#explain)
</quiz>

<quiz>
Когда `LIKE '%value%'` не использует индекс?

- [ ] Всегда
- [x] Когда `%` стоит в начале
- [ ] Когда `%` стоит в конце
- [ ] Только в MySQL

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 3.4 «Когда индекс НЕ помогает»](11-sql-performance.md#когда-индекс-не-помогает)
</quiz>

<quiz>
Что такое партиционирование?

- [ ] Удаление данных
- [x] Разбиение таблицы на части по ключу
- [ ] Создание индекса
- [ ] Резервное копирование

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 6 «Партиционирование»](11-sql-performance.md#6-партиционирование)
</quiz>

<quiz>
Для какого статуса заказов имеет смысл создать частичный индекс?

- [ ] `cancelled`
- [x] `paid`
- [ ] `deleted`
- [ ] `archived`

📖 [11-sql-performance.md](11-sql-performance.md) → [раздел 3.3 «Частичный индекс»](11-sql-performance.md#частичный-индекс)
</quiz>

---

## <a id="sql-даты-и-tz">SQL: Даты и TZ</a>

📖 **Перечитать:** [12-sql-dates.md](12-sql-dates.md)

<quiz>
Какой тип данных хранит дату и время с часовым поясом в PostgreSQL?

- [ ] `DATE`
- [ ] `TIMESTAMP`
- [x] `TIMESTAMPTZ`
- [ ] `TIME`

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 3 «TIMESTAMP vs TIMESTAMPTZ»](12-sql-dates.md#3-timestamp-vs-timestamptz)
</quiz>

<quiz>
Что делает `DATE_TRUNC('month', created_at)`?

- [ ] Возвращает день
- [x] Усекает дату до первого числа месяца
- [ ] Возвращает месяц как число
- [ ] Удаляет дату

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 4.3 «Усечение до периода»](12-sql-dates.md#усечение-до-периода)
</quiz>

<quiz>
Какая функция в PostgreSQL возвращает текущую дату и время?

- [ ] `CURRENT_DATE`
- [x] `NOW()`
- [ ] `SYSDATE`
- [ ] `GETDATE()`

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 4.1 «Текущее время»](12-sql-dates.md#текущее-время)
</quiz>

<quiz>
Зачем нужен `GENERATE_SERIES` в отчётах?

- [ ] Для удаления пропусков
- [x] Для генерации полного списка дат, включая пустые
- [ ] Для соединения таблиц
- [ ] Для агрегации

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 7 «Генерация дат»](12-sql-dates.md#7-генерация-дат)
</quiz>

<quiz>
Что вернёт `NOW() - INTERVAL '7 days'`?

- [ ] Текущую дату
- [x] Дату 7 дней назад
- [ ] Дату 7 дней вперёд
- [ ] Ошибку

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 6 «Интервалы»](12-sql-dates.md#6-интервалы)
</quiz>

<quiz>
Как привести время к московскому поясу?

- [x] `AT TIME ZONE 'Europe/Moscow'`
- [ ] `TIME_ZONE('MSK')`
- [ ] `CONVERT_TZ('MSK')`
- [ ] `TO_MOSCOW()`

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 5 «Часовые пояса»](12-sql-dates.md#5-часовые-пояса)
</quiz>

<quiz>
Какая функция усекает дату до нужного периода (day, week, month, year)?

- [ ] `EXTRACT`
- [x] `DATE_TRUNC`
- [ ] `DATE_PART`
- [ ] `TO_CHAR`

📖 [12-sql-dates.md](12-sql-dates.md) → [раздел 4.3 «Усечение до периода»](12-sql-dates.md#усечение-до-периода)
</quiz>

---

## <a id="sql-диалекты-субд">SQL: Диалекты СУБД</a>

📖 **Перечитать:** [13-sql-dialects.md](13-sql-dialects.md)

<quiz>
Как ограничить выборку в MS SQL?

- [ ] `LIMIT 10`
- [x] `SELECT TOP 10`
- [ ] `FETCH FIRST 10`
- [ ] `ROWNUM <= 10`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 3 «Ограничение строк»](13-sql-dialects.md#3-ограничение-строк)
</quiz>

<quiz>
Какая функция заменяет NULL в Oracle?

- [ ] `ISNULL`
- [ ] `IFNULL`
- [x] `NVL`
- [ ] `COALESCE` только

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 6 «Работа с NULL»](13-sql-dialects.md#6-работа-с-null)
</quiz>

<quiz>
Как в MySQL объявляется автоинкрементный столбец?

- [ ] `SERIAL`
- [x] `AUTO_INCREMENT`
- [ ] `IDENTITY`
- [ ] `SEQUENCE`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 2 «Сравнительная таблица»](13-sql-dialects.md#2-сравнительная-таблица)
</quiz>

<quiz>
Как ограничить выборку в Oracle?

- [ ] `LIMIT 10`
- [ ] `TOP 10`
- [x] `FETCH FIRST 10 ROWS ONLY`
- [ ] `FIRST 10`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 3 «Ограничение строк»](13-sql-dialects.md#3-ограничение-строк)
</quiz>

<quiz>
Что работает во всех СУБД для замены NULL?

- [ ] `ISNULL`
- [ ] `NVL`
- [x] `COALESCE`
- [ ] `IFNULL`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 6 «Работа с NULL»](13-sql-dialects.md#6-работа-с-null)
</quiz>

<quiz>
Как в MySQL реализован UPSERT?

- [ ] `ON CONFLICT`
- [x] `ON DUPLICATE KEY UPDATE`
- [ ] `MERGE`
- [ ] `UPSERT INTO`

📖 [13-sql-dialects.md](13-sql-dialects.md) → [раздел 7 «UPSERT»](13-sql-dialects.md#7-upsert)
</quiz>

---

## <a id="sql-аналитика">SQL: Аналитика</a>

📖 **Перечитать:** [14-sql-analytics.md](14-sql-analytics.md)

<quiz>
Зачем нужна `PERCENTILE_CONT(0.5)`?

- [ ] Для среднего
- [x] Для медианы
- [ ] Для моды
- [ ] Для суммы

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 2 «Перцентили и медиана»](14-sql-analytics.md#2-перцентили-и-медиана)
</quiz>

<quiz>
Чем медиана лучше среднего?

- [ ] Она точнее
- [x] Она устойчива к выбросам
- [ ] Она быстрее
- [ ] Она работает только с числами

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 2 «Перцентили и медиана»](14-sql-analytics.md#2-перцентили-и-медиана)
</quiz>

<quiz>
Что такое retention?

- [ ] Возврат товара
- [x] Доля пользователей, вернувшихся через N дней
- [ ] Отток клиентов
- [ ] Стоимость привлечения

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 5 «Retention»](14-sql-analytics.md#5-retention)
</quiz>

<quiz>
Какая функция разбивает строки на N групп одинакового размера?

- [ ] `RANK`
- [x] `NTILE`
- [ ] `ROW_NUMBER`
- [ ] `DENSE_RANK`

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 2 «NTILE — разбить на группы»](14-sql-analytics.md#ntile-разбить-на-группы)
</quiz>

<quiz>
Что такое когортный анализ?

- [ ] Группировка по региону
- [x] Группировка пользователей по общему признаку (например, месяц регистрации)
- [ ] Сравнение двух периодов
- [ ] Прогноз

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 4 «Когортный анализ»](14-sql-analytics.md#4-когортный-анализ)
</quiz>

<quiz>
Что делают `PERCENTILE_CONT` и `PERCENTILE_DISC`?

- [ ] Считают моду
- [x] Считают перцентили (интерполяция / дискретное значение)
- [ ] Считают среднее
- [ ] Работают как `AVG`

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 2.3 «PERCENTILE_CONT vs PERCENTILE_DISC»](14-sql-analytics.md#percentile-cont-vs-percentile-disc)
</quiz>

<quiz>
Что такое RFM?

- [x] Recency, Frequency, Monetary
- [ ] Ratio, Factor, Mean
- [ ] Range, Formula, Model
- [ ] Report, Filter, Map

📖 [14-sql-analytics.md](14-sql-analytics.md) → [раздел 7 «RFM-анализ»](14-sql-analytics.md#7-rfm-анализ)
</quiz>

---

## <a id="api-rest-и-http">API: REST и HTTP</a>

📖 **Перечитать:** [05-api-rest.md](05-api-rest.md) и [15-api-http-deep.md](15-api-http-deep.md)

<quiz>
Какой HTTP-метод идемпотентен?

- [ ] `POST`
- [x] `PUT`
- [ ] `PATCH`
- [ ] Ни один

📖 [05-api-rest.md](05-api-rest.md) → [раздел 4 «HTTP-методы»](05-api-rest.md#4-http-методы)
</quiz>

<quiz>
Что означает статус-код `409 Conflict`?

- [ ] Ошибка валидации
- [ ] Ресурс не найден
- [x] Конфликт (например, дубль)
- [ ] Нет прав

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 5 «4xx — ошибка клиента»](15-api-http-deep.md#4xx-ошибка-клиента)
</quiz>

<quiz>
В каком заголовке передаётся токен авторизации?

- [ ] `Content-Type`
- [x] `Authorization`
- [ ] `Accept`
- [ ] `User-Agent`

📖 [05-api-rest.md](05-api-rest.md) → [раздел 3.2 «REST: основные понятия»](05-api-rest.md#6-структура-запроса)
</quiz>

<quiz>
Какой HTTP-метод используется для частичного обновления ресурса?

- [ ] `PUT`
- [x] `PATCH`
- [ ] `POST`
- [ ] `GET`

📖 [05-api-rest.md](05-api-rest.md) → [раздел 4 «HTTP-методы»](05-api-rest.md#4-http-методы)
</quiz>

<quiz>
Какой статус-код возвращается при успешном создании ресурса?

- [ ] `200`
- [x] `201`
- [ ] `202`
- [ ] `204`

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 5 «2xx — успех»](15-api-http-deep.md#2xx-успех)
</quiz>

<quiz>
Что означает `401 Unauthorized`?

- [ ] Нет прав
- [x] Не аутентифицирован
- [ ] Ресурс не найден
- [ ] Ошибка сервера

📖 [06-api-auth.md](06-api-auth.md) → [раздел 1 «Аутентификация vs авторизация»](06-api-auth.md#1-аутентификация-vs-авторизация)
</quiz>

<quiz>
Что означает `403 Forbidden`?

- [ ] Не аутентифицирован
- [x] Аутентифицирован, но нет прав
- [ ] Ресурс не найден
- [ ] Таймаут

📖 [06-api-auth.md](06-api-auth.md) → [раздел 1 «Аутентификация vs авторизация»](06-api-auth.md#1-аутентификация-vs-авторизация)
</quiz>

<quiz>
Какой заголовок указывает формат тела запроса?

- [ ] `Accept`
- [x] `Content-Type`
- [ ] `Authorization`
- [ ] `User-Agent`

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 6 «Заголовки»](15-api-http-deep.md#5-заголовки)
</quiz>

---

## <a id="api-аутентификация">API: Аутентификация</a>

📖 **Перечитать:** [06-api-auth.md](06-api-auth.md)

<quiz>
Чем аутентификация отличается от авторизации?

- [ ] Ничем
- [x] Аутентификация — «кто ты», авторизация — «что тебе можно»
- [ ] Аутентификация — про роли
- [ ] Авторизация — про пароли

📖 [06-api-auth.md](06-api-auth.md) → [раздел 1 «Аутентификация vs авторизация»](06-api-auth.md#1-аутентификация-vs-авторизация)
</quiz>

<quiz>
Что такое JWT?

- [ ] Формат шифрования
- [x] Токен из трёх частей: header.payload.signature
- [ ] Протокол
- [ ] Тип БД

📖 [06-api-auth.md](06-api-auth.md) → [раздел 5 «JWT»](06-api-auth.md#5-jwt-json-web-token)
</quiz>

<quiz>
Какой тип токена указывается в заголовке `Authorization` для JWT?

- [ ] `Basic`
- [x] `Bearer`
- [ ] `Token`
- [ ] `JWT`

📖 [06-api-auth.md](06-api-auth.md) → [раздел 5 «JWT»](06-api-auth.md#5-jwt-json-web-token)
</quiz>

<quiz>
Что такое OAuth 2.0?

- [ ] Тип API
- [x] Протокол делегированной авторизации
- [ ] Формат данных
- [ ] База данных

📖 [06-api-auth.md](06-api-auth.md) → [раздел 4 «OAuth 2.0»](06-api-auth.md#4-oauth-2-0)
</quiz>

<quiz>
Чем отличается `access_token` от `refresh_token`?

- [ ] Ничем
- [x] `access_token` — короткий доступ, `refresh_token` — долгий, для обновления
- [ ] `refresh_token` — короче
- [ ] `access_token` — только для админов

📖 [06-api-auth.md](06-api-auth.md) → [раздел 4 «Токены»](06-api-auth.md#токены)
</quiz>

<quiz>
Что вернёт сервер при истечении токена?

- [ ] `403`
- [x] `401` с кодом `TOKEN_EXPIRED`
- [ ] `500`
- [ ] `404`

📖 [06-api-auth.md](06-api-auth.md) → [раздел 6 «Что описывать аналитику»](06-api-auth.md#6-что-описывать-аналитику)
</quiz>

---

## API: OpenAPI

📖 **Перечитать:** [07-api-openapi.md](07-api-openapi.md)

<quiz>
Что такое OpenAPI?

- [ ] Тип API
- [x] Стандарт описания REST API в YAML/JSON
- [ ] Протокол
- [ ] База данных

📖 [07-api-openapi.md](07-api-openapi.md) → [раздел 1 «Что такое OpenAPI»](07-api-openapi.md#1-что-такое-openapi)
</quiz>

<quiz>
Как называется раздел спецификации OpenAPI, в котором описываются схемы данных?

- [ ] `paths`
- [x] `components`
- [ ] `schemas`
- [ ] `definitions`

📖 [07-api-openapi.md](07-api-openapi.md) → [раздел 4 «Схемы данных»](07-api-openapi.md#4-схемы-данных-components)
</quiz>

<quiz>
Как в OpenAPI указать, что поле обязательное?

- [ ] Через `required: true`
- [x] Через `required: [field]` на уровне схемы
- [ ] Через `!` в имени
- [ ] Через `not-null`

📖 [07-api-openapi.md](07-api-openapi.md) → [раздел 4 «Схемы данных»](07-api-openapi.md#4-схемы-данных-components)
</quiz>

<quiz>
Зачем нужен Swagger UI?

- [ ] Для написания кода
- [x] Для просмотра и тестирования API по спецификации
- [ ] Для деплоя
- [ ] Для логирования

📖 [07-api-openapi.md](07-api-openapi.md) → [раздел 7 «Инструменты»](07-api-openapi.md#7-инструменты)
</quiz>

<quiz>
Как называется схема, на которую ссылается `$ref: '#/components/schemas/____'`?

- [ ] `User`
- [x] `Order`
- [ ] `Product`
- [ ] `Payment`

📖 [07-api-openapi.md](07-api-openapi.md) → [раздел 4 «Схемы данных»](07-api-openapi.md#4-схемы-данных-components)
</quiz>

---

## <a id="api-интеграции">API: Интеграции</a>

📖 **Перечитать:** [08-api-integrations.md](08-api-integrations.md)

<quiz>
Чем webhook отличается от polling?

- [ ] Webhook медленнее
- [x] Webhook отправляет событие сразу, polling — опрашивает
- [ ] Webhook использует SOAP
- [ ] Ничем

📖 [08-api-integrations.md](08-api-integrations.md) → [раздел 4 «Webhooks»](08-api-integrations.md#4-webhooks)
</quiz>

<quiz>
Как проверить подлинность webhook?

- [ ] По IP-адресу
- [x] По HMAC-подписи
- [ ] По User-Agent
- [ ] По размеру тела

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 5 «Безопасность»](18-api-webhooks-deep.md#5-безопасность)
</quiz>

<quiz>
Что такое Dead Letter Queue (DLQ)?

- [ ] Очередь для успешных сообщений
- [x] Очередь для необработанных сообщений
- [ ] Очередь для приоритетных сообщений
- [ ] Очередь для удалённых сообщений

📖 [08-api-integrations.md](08-api-integrations.md) → [раздел 7 «Обработка ошибок»](08-api-integrations.md#7-обработка-ошибок)
</quiz>

<quiz>
Куда попадает сообщение при асинхронной интеграции?

- [ ] В базу данных
- [x] В очередь
- [ ] В кэш
- [ ] В лог

📖 [08-api-integrations.md](08-api-integrations.md) → [раздел 3 «Асинхронные интеграции»](08-api-integrations.md#3-асинхронные-интеграции)
</quiz>

<quiz>
Что такое маппинг полей?

- [ ] Создание полей
- [x] Таблица соответствия полей между системами
- [ ] Удаление полей
- [ ] Индексация

📖 [08-api-integrations.md](08-api-integrations.md) → [раздел 8 «Маппинг данных»](08-api-integrations.md#8-маппинг-данных)
</quiz>

<quiz>
Что описывает аналитик в ТЗ для интеграции?

- [ ] Только endpoint
- [x] Формат данных, сценарии, ошибки, маппинг, retry
- [ ] Только ошибки
- [ ] Только схему БД

📖 [09-sql-api-workflow.md](09-sql-api-workflow.md) → [раздел 4 «Шаблоны документов»](09-sql-api-workflow.md#4-шаблоны-документов)
</quiz>

<quiz>
Что такое идемпотентность?

- [ ] Скорость работы
- [x] Свойство: повторный вызов даёт тот же результат
- [ ] Тип авторизации
- [ ] Формат данных

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 2 «Что такое идемпотентность»](17-api-idempotency.md#2-что-такое-идемпотентность)
</quiz>

<quiz>
Какой формат файла, кроме CSV и XML, часто используется в пакетном обмене?

- [ ] YAML
- [x] JSON
- [ ] TOML
- [ ] INI

📖 [08-api-integrations.md](08-api-integrations.md) → [раздел 6 «Пакетный обмен»](08-api-integrations.md#6-пакетный-обмен)
</quiz>

---

## <a id="api-http-глубоко">API: HTTP глубоко</a>

📖 **Перечитать:** [15-api-http-deep.md](15-api-http-deep.md)

<quiz>
Что такое идемпотентность метода?

- [ ] Метод быстрый
- [x] Повторный вызов даёт тот же результат
- [ ] Метод безопасен
- [ ] Метод кэшируется

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 3 «Методы HTTP»](15-api-http-deep.md#3-методы-http)
</quiz>

<quiz>
Какой метод безопасный (не меняет состояние)?

- [ ] `POST`
- [x] `GET`
- [ ] `PUT`
- [ ] `DELETE`

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 3 «Методы HTTP»](15-api-http-deep.md#3-методы-http)
</quiz>

<quiz>
Что такое CORS?

- [ ] Тип авторизации
- [x] Механизм, разрешающий браузеру обращаться к чужому домену
- [ ] Формат данных
- [ ] Протокол

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 8 «CORS»](15-api-http-deep.md#8-cors)
</quiz>

<quiz>
Какой заголовок вместе с `Cache-Control` используется для условных запросов?

- [ ] `Location`
- [x] `ETag`
- [ ] `Content-Length`
- [ ] `Retry-After`

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 9 «Кэширование»](15-api-http-deep.md#9-кэширование)
</quiz>

<quiz>
Что означает `304 Not Modified`?

- [ ] Ошибка
- [x] Кэш клиента актуален
- [ ] Ресурс удалён
- [ ] Редирект

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 9 «Кэширование»](15-api-http-deep.md#9-кэширование)
</quiz>

<quiz>
Какой заголовок сообщает о лимите запросов?

- [ ] `X-Rate-Limit`
- [x] `X-RateLimit-Limit`
- [ ] `Rate-Limit-Max`
- [ ] `Limit-Requests`

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 6 «Response headers»](15-api-http-deep.md#response-headers)
</quiz>

<quiz>
Что такое content negotiation?

- [x] Согласование контента между клиентом и сервером через `Accept`
- [ ] Создание контента
- [ ] Удаление контента
- [ ] Кэширование

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 7 «Content Negotiation»](15-api-http-deep.md#6-content-negotiation)
</quiz>

<quiz>
Что передаётся в заголовке `Authorization: Bearer <...>`?

- [ ] Логин
- [x] Токен
- [ ] Пароль
- [ ] API-ключ

📖 [15-api-http-deep.md](15-api-http-deep.md) → [раздел 6 «Request headers»](15-api-http-deep.md#request-headers)
</quiz>

---

## <a id="api-паттерны-проектирования">API: Паттерны проектирования</a>

📖 **Перечитать:** [16-api-design-patterns.md](16-api-design-patterns.md)

<quiz>
Какой URL соответствует REST-соглашениям?

- [ ] `/getUsers`
- [x] `/users`
- [ ] `/users/list`
- [ ] `/user_list`

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 2 «Именование ресурсов»](16-api-design-patterns.md#2-именование-ресурсов)
</quiz>

<quiz>
Что такое cursor-based пагинация?

- [ ] По номеру страницы
- [x] По курсору (например, `after_id`)
- [ ] По offset
- [ ] По дате

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 3 «Пагинация»](16-api-design-patterns.md#3-пагинация)
</quiz>

<quiz>
Что должно быть в ответе при ошибке?

- [ ] Только HTTP-статус
- [ ] Только текст
- [x] Код, сообщение, детали
- [ ] HTML

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 6 «Формат ошибок»](16-api-design-patterns.md#6-формат-ошибок)
</quiz>

<quiz>
Какой префикс в query-параметре означает сортировку по убыванию?

- [ ] `+`
- [x] `-`
- [ ] `#`
- [ ] `@`

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 4 «Фильтрация и сортировка»](16-api-design-patterns.md#4-фильтрация-и-сортировка)
</quiz>

<quiz>
Что такое bulk-операция?

- [x] Массовая операция над несколькими объектами
- [ ] Операция с одним объектом
- [ ] Операция с БД
- [ ] Операция с файлами

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 7 «Bulk-операции»](16-api-design-patterns.md#7-bulk-операции)
</quiz>

<quiz>
Что такое breaking change?

- [ ] Улучшение API
- [x] Изменение, несовместимое с предыдущей версией
- [ ] Добавление поля
- [ ] Новый endpoint

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 8 «Версионирование»](16-api-design-patterns.md#8-версионирование)
</quiz>

<quiz>
В какое поле обычно оборачивают коллекцию в ответе API?

- [ ] `items`
- [x] `data`
- [ ] `list`
- [ ] `results`

📖 [16-api-design-patterns.md](16-api-design-patterns.md) → [раздел 5 «Формат ответа»](16-api-design-patterns.md#5-формат-ответа)
</quiz>

---

## <a id="api-идемпотентность">API: Идемпотентность</a>

📖 **Перечитать:** [17-api-idempotency.md](17-api-idempotency.md)

<quiz>
Зачем нужен `Idempotency-Key`?

- [ ] Для авторизации
- [x] Для защиты от дублей при повторных запросах
- [ ] Для кэширования
- [ ] Для логирования

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 4 «Idempotency-Key»](17-api-idempotency.md#4-idempotency-key)
</quiz>

<quiz>
Какой HTTP-код нужно повторить (retry)?

- [ ] `400`
- [ ] `401`
- [x] `500`
- [ ] `404`

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 5 «Когда повторять»](17-api-idempotency.md#когда-повторять)
</quiz>

<quiz>
Что такое экспоненциальный backoff?

- [x] Увеличение задержки между попытками с каждой попыткой
- [ ] Уменьшение задержки
- [ ] Постоянная задержка
- [ ] Отсутствие задержки

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 6 «Backoff и jitter»](17-api-idempotency.md#6-backoff-и-jitter)
</quiz>

<quiz>
Какой HTTP-код возвращается при превышении лимита запросов?

- [ ] `403`
- [x] `429`
- [ ] `503`
- [ ] `400`

📖 [24-api-security.md](24-api-security.md) → [раздел 6 «Rate limiting»](24-api-security.md#6-rate-limiting)
</quiz>

<quiz>
Что такое Circuit Breaker?

- [ ] Тип авторизации
- [x] Механизм защиты от повторных вызовов неработающего сервиса
- [ ] Формат данных
- [ ] Тип БД

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 7 «Circuit Breaker»](17-api-idempotency.md#7-circuit-breaker)
</quiz>

<quiz>
Что такое at-least-once?

- [ ] Сообщение может потеряться
- [x] Сообщение доставится, но может задвоиться
- [ ] Доставится ровно один раз
- [ ] Не доставится никогда

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 9 «Гарантии доставки»](17-api-idempotency.md#9-гарантии-доставки)
</quiz>

<quiz>
Какой заголовок клиент передаёт для защиты от дублей?

- [ ] `X-Request-Id`
- [x] `Idempotency-Key`
- [ ] `Authorization`
- [ ] `Content-Type`

📖 [17-api-idempotency.md](17-api-idempotency.md) → [раздел 4 «Idempotency-Key»](17-api-idempotency.md#4-idempotency-key)
</quiz>

---

## API: Webhooks

📖 **Перечитать:** [18-api-webhooks-deep.md](18-api-webhooks-deep.md)

<quiz>
Что такое webhook?

- [ ] Синхронный запрос
- [x] HTTP-уведомление о событии
- [ ] Тип БД
- [ ] Формат данных

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 2 «Что такое webhook»](18-api-webhooks-deep.md#2-что-такое-webhook)
</quiz>

<quiz>
Что считается успешной доставкой webhook?

- [ ] `200`
- [x] Любой `2xx`
- [ ] `3xx`
- [ ] `4xx`

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 6 «Retry и доставка»](18-api-webhooks-deep.md#6-retry-и-доставка)
</quiz>

<quiz>
Гарантирован ли порядок доставки webhooks?

- [ ] Да, всегда
- [x] Нет, не гарантирован
- [ ] Только для одного события
- [ ] Зависит от сервера

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 8 «Порядок доставки»](18-api-webhooks-deep.md#8-порядок-доставки)
</quiz>

<quiz>
В каком заголовке передаётся HMAC-подпись webhook?

- [ ] `X-Token`
- [x] `X-Signature`
- [ ] `X-Auth`
- [ ] `X-Hash`

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 5 «Безопасность»](18-api-webhooks-deep.md#5-безопасность)
</quiz>

<quiz>
Как обрабатывать повторные webhooks?

- [ ] Игнорировать
- [x] Хранить `event_id` и игнорировать дубли
- [ ] Отвечать `500`
- [ ] Перезапустить сервис

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 7 «Идемпотентность»](18-api-webhooks-deep.md#7-идемпотентность)
</quiz>

<quiz>
Что делать, если webhook вернул `500`?

- [ ] Не повторять
- [x] Повторить с backoff
- [ ] Удалить подписку
- [ ] Отправить письмо

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 6 «Retry и доставка»](18-api-webhooks-deep.md#6-retry-и-доставка)
</quiz>

<quiz>
Какое поле в payload webhook указывает тип события?

- [ ] `type`
- [x] `event`
- [ ] `action`
- [ ] `name`

📖 [18-api-webhooks-deep.md](18-api-webhooks-deep.md) → [раздел 4 «Формат payload»](18-api-webhooks-deep.md#4-формат-payload)
</quiz>

---

## <a id="api-очереди-и-брокеры">API: Очереди и брокеры</a>

📖 **Перечитать:** [19-api-messaging.md](19-api-messaging.md)

<quiz>
Чем Kafka отличается от RabbitMQ?

- [ ] Ничем
- [x] Kafka — распределённый лог, RabbitMQ — брокер очередей
- [ ] Kafka только для Python
- [ ] RabbitMQ быстрее

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 4 «Kafka»](19-api-messaging.md#4-kafka) и раздел 5 «RabbitMQ»
</quiz>

<quiz>
Что такое partition в Kafka?

- [ ] Тип сообщения
- [x] Часть топика для параллелизма
- [ ] Формат данных
- [ ] Потребитель

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 4 «Kafka»](19-api-messaging.md#4-kafka)
</quiz>

<quiz>
Что такое consumer group?

- [ ] Группа producer'ов
- [x] Группа consumer'ов, читающих из топика
- [ ] Тип топика
- [ ] Часть сообщения

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 4 «Kafka»](19-api-messaging.md#4-kafka)
</quiz>

<quiz>
Куда попадает сообщение при асинхронной обработке, если это не топик?

- [ ] В базу данных
- [x] В очередь
- [ ] В кэш
- [ ] В лог

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 2 «Что такое очередь»](19-api-messaging.md#2-что-такое-очередь)
</quiz>

<quiz>
Что такое Outbox-паттерн?

- [ ] Тип индекса
- [x] Запись события в БД вместе с данными для последующей публикации
- [ ] Формат данных
- [ ] Тип авторизации

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 8 «Outbox»](19-api-messaging.md#outbox)
</quiz>

<quiz>
Что такое Saga?

- [ ] Тип БД
- [x] Распределённая транзакция через последовательность событий
- [ ] Протокол
- [ ] Формат данных

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 8 «Saga»](19-api-messaging.md#saga)
</quiz>

<quiz>
Как называется паттерн, где одно сообщение получают несколько подписчиков?

- [ ] Point-to-Point
- [x] Pub/Sub
- [ ] Competing Consumers
- [ ] DLQ

📖 [19-api-messaging.md](19-api-messaging.md) → [раздел 8 «Pub/Sub»](19-api-messaging.md#pub-sub)
</quiz>

---

## <a id="api-тестирование">API: Тестирование</a>

📖 **Перечитать:** [20-api-testing.md](20-api-testing.md)

<quiz>
Что такое Postman?

- [ ] Язык программирования
- [x] Инструмент для тестирования API
- [ ] База данных
- [ ] Формат данных

📖 [20-api-testing.md](20-api-testing.md) → [раздел 3 «Postman»](20-api-testing.md#3-postman)
</quiz>

<quiz>
Что такое contract testing?

- [ ] Проверка скорости
- [x] Проверка соответствия контракту между клиентом и сервером
- [ ] Проверка кода
- [ ] Проверка безопасности

📖 [20-api-testing.md](20-api-testing.md) → [раздел 4 «Contract testing»](20-api-testing.md#4-contract-testing)
</quiz>

<quiz>
Что такое mock-сервер?

- [ ] Реальный API
- [x] Фейковый API, отвечающий по спецификации
- [ ] Прокси
- [ ] База данных

📖 [20-api-testing.md](20-api-testing.md) → [раздел 5 «Mock-серверы»](20-api-testing.md#5-mock-серверы)
</quiz>

<quiz>
Какая метрика latency показывает 95-й перцентиль?

- [ ] `p50`
- [x] `p95`
- [ ] `p99`
- [ ] `avg`

📖 [20-api-testing.md](20-api-testing.md) → [раздел 6 «Нагрузочное тестирование»](20-api-testing.md#6-нагрузочное-тестирование)
</quiz>

<quiz>
Что должен проверять аналитик в edge cases?

- [ ] Только успех
- [x] Пустые данные, невалидные поля, ошибки, дубли
- [ ] Только ошибки сервера
- [ ] Только нагрузку

📖 [20-api-testing.md](20-api-testing.md) → [раздел 7 «Проверка edge cases»](20-api-testing.md#7-проверка-edge-cases)
</quiz>

<quiz>
Что такое Newman?

- [ ] Тип API
- [x] CLI-версия Postman
- [ ] Формат данных
- [ ] Язык

📖 [20-api-testing.md](20-api-testing.md) → [раздел 3 «Newman»](20-api-testing.md#newman)
</quiz>

---

## API: GraphQL / gRPC / WebSocket

📖 **Перечитать:** [21-api-graphql-grpc.md](21-api-graphql-grpc.md)

<quiz>
Чем GraphQL отличается от REST?

- [ ] Ничем
- [x] Клиент сам выбирает нужные поля
- [ ] GraphQL только для Python
- [ ] REST быстрее

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 2 «GraphQL»](21-api-graphql-grpc.md#graphql)
</quiz>

<quiz>
Что такое gRPC?

- [ ] Тип авторизации
- [x] RPC-фреймворк на HTTP/2 + Protocol Buffers
- [ ] Формат данных
- [ ] Тип БД

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 3 «gRPC»](21-api-graphql-grpc.md#grpc)
</quiz>

<quiz>
Что такое WebSocket?

- [ ] Односторонний канал
- [x] Двусторонний канал поверх TCP
- [ ] HTTP-запрос
- [ ] Формат данных

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 4 «WebSocket»](21-api-graphql-grpc.md#websocket)
</quiz>

<quiz>
Как называется операция в GraphQL для чтения данных?

- [ ] `mutation`
- [x] `query`
- [ ] `subscription`
- [ ] `fetch`

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 2 «GraphQL»](21-api-graphql-grpc.md#graphql)
</quiz>

<quiz>
Что такое SSE?

- [ ] Двусторонний канал
- [x] Односторонний поток от сервера к клиенту по HTTP
- [ ] Тип БД
- [ ] Формат данных

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 5 «Server-Sent Events»](21-api-graphql-grpc.md#5-server-sent-events-sse)
</quiz>

<quiz>
Какое расширение у файла с контрактом gRPC?

- [ ] `.graphql`
- [x] `.proto`
- [ ] `.thrift`
- [ ] `.avro`

📖 [21-api-graphql-grpc.md](21-api-graphql-grpc.md) → [раздел 3 «gRPC»](21-api-graphql-grpc.md#grpc)
</quiz>

---

## <a id="api-кэширование">API: Кэширование</a>

📖 **Перечитать:** [22-api-caching.md](22-api-caching.md)

<quiz>
Что делает `Cache-Control: no-store`?

- [ ] Кэширует навсегда
- [x] Запрещает кэширование
- [ ] Кэширует только в браузере
- [ ] Удаляет кэш

📖 [22-api-caching.md](22-api-caching.md) → [раздел 4 «Cache-Control»](22-api-caching.md#4-cache-control)
</quiz>

<quiz>
Что такое ETag?

- [ ] Тип авторизации
- [x] Хэш версии ресурса для условных запросов
- [ ] Формат данных
- [ ] Индекс

📖 [22-api-caching.md](22-api-caching.md) → [раздел 5 «ETag и условные запросы»](22-api-caching.md#5-etag-и-условные-запросы)
</quiz>

<quiz>
Что означает `private` в `Cache-Control`?

- [ ] Кэшируется везде
- [x] Кэшируется только в браузере
- [ ] Не кэшируется
- [ ] Кэшируется на CDN

📖 [22-api-caching.md](22-api-caching.md) → [раздел 4 «Cache-Control»](22-api-caching.md#4-cache-control)
</quiz>

<quiz>
Какой статус-код возвращает сервер, если ресурс не изменился?

- [ ] `200`
- [x] `304`
- [ ] `404`
- [ ] `500`

📖 [22-api-caching.md](22-api-caching.md) → [раздел 5 «ETag и условные запросы»](22-api-caching.md#5-etag-и-условные-запросы)
</quiz>

<quiz>
Что такое cache stampede?

- [ ] Медленное кэширование
- [x] Массовое истребование отсутствующего ключа
- [ ] Удаление кэша
- [ ] Тип БД

📖 [22-api-caching.md](22-api-caching.md) → [раздел 8 «Проблемы»](22-api-caching.md#проблемы)
</quiz>

<quiz>
Что такое Redis?

- [ ] Тип API
- [x] In-memory хранилище для кэша
- [ ] Формат данных
- [ ] Брокер сообщений

📖 [22-api-caching.md](22-api-caching.md) → [раздел 8 «Redis»](22-api-caching.md#8-redis)
</quiz>

---

## <a id="api-мониторинг">API: Мониторинг</a>

📖 **Перечитать:** [23-api-monitoring.md](23-api-monitoring.md)

<quiz>
Что такое три столпа наблюдаемости?

- [x] Logs, Metrics, Traces
- [ ] Users, Tables, Files
- [ ] Code, Tests, Docs
- [ ] CPU, RAM, Disk

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 2 «Три столпа наблюдаемости»](23-api-monitoring.md#2-три-столпа-наблюдаемости)
</quiz>

<quiz>
Что такое SLI?

- [ ] Обязательство
- [x] Индикатор, который измеряем
- [ ] Цель
- [ ] Алерт

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 6 «SLI, SLO, SLA»](23-api-monitoring.md#6-sli-slo-sla)
</quiz>

<quiz>
Что такое SLO?

- [ ] Индикатор
- [x] Целевое значение SLI
- [ ] Обязательство перед клиентом
- [ ] Лог

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 6 «SLI, SLO, SLA»](23-api-monitoring.md#6-sli-slo-sla)
</quiz>

<quiz>
В каком формате обычно пишут структурированные логи?

- [ ] XML
- [x] JSON
- [ ] YAML
- [ ] CSV

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 3 «Логи»](23-api-monitoring.md#3-логи)
</quiz>

<quiz>
Что такое distributed tracing?

- [ ] Логирование
- [x] Трассировка пути запроса через микросервисы
- [ ] Метрики
- [ ] Алерт

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 5 «Трассировка»](23-api-monitoring.md#5-трассировка)
</quiz>

<quiz>
Зачем нужен `X-Request-Id`?

- [ ] Для авторизации
- [x] Для трассировки запроса между сервисами
- [ ] Для кэша
- [ ] Для rate limiting

📖 [23-api-monitoring.md](23-api-monitoring.md) → [раздел 5 «Трассировка»](23-api-monitoring.md#5-трассировка)
</quiz>

---

## <a id="api-безопасность">API: Безопасность</a>

📖 **Перечитать:** [24-api-security.md](24-api-security.md)

<quiz>
Что такое BOLA (Broken Object Level Authorization)?

- [ ] Ошибка в токене
- [x] Пользователь получает доступ к чужому объекту
- [ ] Ошибка в заголовках
- [ ] Утечка данных через логи

📖 [24-api-security.md](24-api-security.md) → [раздел 2 «OWASP API Top 10»](24-api-security.md#2-owasp-api-top-10)
</quiz>

<quiz>
Зачем нужен rate limiting?

- [ ] Для ускорения
- [x] Для защиты от перегрузки и брутфорса
- [ ] Для кэша
- [ ] Для логирования

📖 [24-api-security.md](24-api-security.md) → [раздел 6 «Rate limiting»](24-api-security.md#6-rate-limiting)
</quiz>

<quiz>
Что такое SQL injection?

- [ ] Тип БД
- [x] Внедрение SQL-кода через пользовательский ввод
- [ ] Тип индекса
- [ ] Формат данных

📖 [24-api-security.md](24-api-security.md) → [раздел 5 «Защита от атак»](24-api-security.md#5-защита-от-атак)
</quiz>

<quiz>
Какие запросы защищают от SQL injection?

- [ ] Динамические
- [x] Параметризованные
- [ ] Конкатенированные
- [ ] Вложенные

📖 [24-api-security.md](24-api-security.md) → [раздел 5 «Защита от атак»](24-api-security.md#5-защита-от-атак)
</quiz>

<quiz>
Что такое CSRF?

- [ ] Тип авторизации
- [x] Подделка межсайтового запроса
- [ ] Тип БД
- [ ] Формат данных

📖 [24-api-security.md](24-api-security.md) → [раздел 5 «Защита от атак»](24-api-security.md#5-защита-от-атак)
</quiz>

<quiz>
Как защититься от mass assignment?

- [ ] Через `SELECT *`
- [x] Через whitelist разрешённых полей
- [ ] Через индексы
- [ ] Через кэш

📖 [24-api-security.md](24-api-security.md) → [раздел 5 «Mass Assignment»](24-api-security.md#mass-assignment)
</quiz>

<quiz>
Что делают с чувствительными полями в логах?

- [ ] Удаляют
- [x] Маскируют
- [ ] Шифруют
- [ ] Хэшируют

📖 [24-api-security.md](24-api-security.md) → [раздел 4 «Работа с чувствительными данными»](24-api-security.md#4-работа-с-чувствительными-данными)
</quiz>

---

<!-- mkdocs-quiz results -->

---

## <a id="о-тестах">📊 О тестах</a>

**Всего вопросов:** ~140  
**Охват:** все 24 учебных файла справочника

### <a id="как-использовать">Как использовать</a>

1. **Терминал** — `mkdocs-quiz run 25-quiz.md`
2. **Браузер** — `pip install mkdocs-quiz` → `mkdocs serve`
3. **Статически** — открыть в редакторе Markdown с поддержкой `<details>`

### <a id="соответствие-разделам-справочника">Соответствие разделам справочника</a>

| Раздел тестов | Файлы справочника |
|---|---|
| SQL: Основы | [01-sql-basics.md](01-sql-basics.md) |
| SQL: JOIN | [02-sql-joins.md](02-sql-joins.md) |
| SQL: Агрегация | [03-sql-aggregation.md](03-sql-aggregation.md) |
| SQL: Продвинутый | [04-sql-advanced.md](04-sql-advanced.md) |
| SQL: DDL / DML / Транзакции | [10-sql-ddl-dml.md](10-sql-ddl-dml.md) |
| SQL: Производительность | [11-sql-performance.md](11-sql-performance.md) |
| SQL: Даты и TZ | [12-sql-dates.md](12-sql-dates.md) |
| SQL: Диалекты СУБД | [13-sql-dialects.md](13-sql-dialects.md) |
| SQL: Аналитика | [14-sql-analytics.md](14-sql-analytics.md) |
| API: REST и HTTP | [05-api-rest.md](05-api-rest.md), [15-api-http-deep.md](15-api-http-deep.md) |
| API: Аутентификация | [06-api-auth.md](06-api-auth.md) |
| API: OpenAPI | [07-api-openapi.md](07-api-openapi.md) |
| API: Интеграции | [08-api-integrations.md](08-api-integrations.md) |
| API: HTTP глубоко | [15-api-http-deep.md](15-api-http-deep.md) |
| API: Паттерны проектирования | [16-api-design-patterns.md](16-api-design-patterns.md) |
| API: Идемпотентность | [17-api-idempotency.md](17-api-idempotency.md) |
| API: Webhooks | [18-api-webhooks-deep.md](18-api-webhooks-deep.md) |
| API: Очереди и брокеры | [19-api-messaging.md](19-api-messaging.md) |
| API: Тестирование | [20-api-testing.md](20-api-testing.md) |
| API: GraphQL / gRPC / WebSocket | [21-api-graphql-grpc.md](21-api-graphql-grpc.md) |
| API: Кэширование | [22-api-caching.md](22-api-caching.md) |
| API: Мониторинг | [23-api-monitoring.md](23-api-monitoring.md) |
| API: Безопасность | [24-api-security.md](24-api-security.md) |

### <a id="рекомендации">Рекомендации</a>

- Проходите тесты **после** изучения соответствующего файла.
- Если ответ неверный — переходите по ссылке в пояснении.
- Прогресс сохраняется в браузере — можно проходить частями.
