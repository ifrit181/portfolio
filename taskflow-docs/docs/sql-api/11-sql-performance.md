# <a id="sql-производительность-и-оптимизация">SQL: производительность и оптимизация</a>

## <a id="содержание">Содержание</a>

1. Зачем аналитику оптимизация
2. Как СУБД выполняет запрос
3. Индексы
4. EXPLAIN / EXPLAIN ANALYZE
5. Антипаттерны
6. Партиционирование
7. Практика
8. Чек-лист

---

## <a id="1-зачем-аналитику-оптимизация">1. Зачем аналитику оптимизация</a>

Аналитик не тюнит продакшн-запросы, но:

- пишет тяжёлые аналитические запросы;
- проверяет данные на больших таблицах;
- согласовывает индексы с DBA;
- понимает, почему отчёт «висит».

Без этого аналитик не отличит рабочий запрос от катастрофы.

---

## <a id="2-как-субд-выполняет-запрос">2. Как СУБД выполняет запрос</a>

Порядок выполнения `SELECT`:

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

**Планировщик** выбирает стратегию:
- **Seq Scan** — последовательное чтение всей таблицы;
- **Index Scan** — чтение по индексу;
- **Bitmap Index Scan** — чтение через битовую карту;
- **Nested Loop / Hash Join / Merge Join** — способы соединения.

Чем меньше строк читается — тем быстрее.

---

## <a id="3-индексы">3. Индексы</a>

**Индекс** — структура для быстрого поиска. Ускоряет `WHERE`, `JOIN`, `ORDER BY`.

### <a id="b-tree-по-умолчанию">B-tree (по умолчанию)</a>

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### <a id="составной-индекс">Составной индекс</a>

```sql
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
```

**Правило:** порядок полей важен. Индекс `(user_id, status)` ускорит:
- `WHERE user_id = 123`
- `WHERE user_id = 123 AND status = 'paid'`

Но не ускорит:
- `WHERE status = 'paid'` (без `user_id`)

### <a id="уникальный-индекс">Уникальный индекс</a>

```sql
CREATE UNIQUE INDEX uq_orders_external ON orders(external_id);
```

### <a id="частичный-индекс">Частичный индекс</a>

```sql
-- индексируем только активные заказы
CREATE INDEX idx_orders_active ON orders(created_at)
WHERE status = 'active';
```

Полезно, когда большая часть данных — «мусор» (удалённые, архивные).

### <a id="когда-индекс-не-помогает">Когда индекс НЕ помогает</a>

- `WHERE LOWER(email) = 'a@b.com'` — функция на поле. Решение: функциональный индекс `CREATE INDEX ON users(LOWER(email))`.
- `WHERE email LIKE '%@gmail.com'` — `%` в начале.
- `WHERE status = 'active'` на таблице с 3 статусами и миллионом строк — планировщик может выбрать Seq Scan.

---

## 4. EXPLAIN / EXPLAIN ANALYZE

### EXPLAIN

Показывает план без выполнения.

```sql
EXPLAIN
SELECT * FROM orders WHERE user_id = 123;
```

**Вывод:**
```
Index Scan using idx_orders_user_id on orders  (cost=0.43..8.45 rows=1 width=64)
  Index Cond: (user_id = 123)
```

### EXPLAIN ANALYZE

Выполняет запрос и показывает реальное время.

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 123;
```

**Вывод:**
```
Index Scan using idx_orders_user_id on orders  (cost=0.43..8.45 rows=1 width=64)
  (actual time=0.015..0.017 rows=1 loops=1)
Planning Time: 0.1 ms
Execution Time: 0.05 ms
```

### <a id="что-искать-в-плане">Что искать в плане</a>

| Признак | Проблема |
|---|---|
| `Seq Scan` на большой таблице | Нет индекса |
| `rows=X` сильно отличается от `actual rows=Y` | Устаревшая статистика (`ANALYZE`) |
| `Nested Loop` с большим количеством loops | Плохой JOIN |
| `Sort` без индекса | `ORDER BY` без индекса |
| `Hash Join` с большим `rows` | Много данных в памяти |

### <a id="analyze-обновить-статистику">ANALYZE — обновить статистику</a>

```sql
ANALYZE orders;
```

Планировщик опирается на статистику. Если данные сильно изменились — её нужно обновить.

---

## <a id="5-антипаттерны">5. Антипаттерны</a>

| Антипаттерн | Почему плохо | Как исправить |
|---|---|---|
| `SELECT *` | Читает лишние поля | Перечислять поля |
| `WHERE YEAR(created_at) = 2026` | Функция мешает индексу | `WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'` |
| `LIKE '%value%'` | Не использует B-tree | Полнотекстовый индекс / `pg_trgm` |
| `NOT IN (SELECT ...)` | Медленно + NULL-риски | `NOT EXISTS` |
| `DISTINCT` без причины | Дорого | Убрать дубли через `GROUP BY` или JOIN |
| `OR` в WHERE | Мешает индексу | `UNION ALL` |
| Подзапрос в SELECT | Выполняется для каждой строки | JOIN или CTE |
| `COUNT(*)` на огромной таблице | Полный скан | Приближённо через `pg_class.reltuples` |

### <a id="пример-or-union-all">Пример: OR → UNION ALL</a>

```sql
-- медленно
SELECT * FROM orders WHERE user_id = 1 OR user_id = 2;

-- быстрее
SELECT * FROM orders WHERE user_id = 1
UNION ALL
SELECT * FROM orders WHERE user_id = 2;
```

---

## <a id="6-партиционирование">6. Партиционирование</a>

Большую таблицу можно разбить на части (по дате, по региону).

```sql
CREATE TABLE orders (
    id BIGSERIAL,
    created_at TIMESTAMPTZ NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2026_01 PARTITION OF orders
FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

**Зачем:**
- быстрее запросы с фильтром по `created_at`;
- проще архивировать (`DROP PARTITION`);
- меньше нагрузка на индексы.

**Что должен понимать аналитик:** если таблица партиционирована, запросы без фильтра по ключу партиционирования будут медленными.

---

## <a id="7-практика">7. Практика</a>

### <a id="задача-1">Задача 1</a>
Запрос выполняется 30 секунд. Как ускорить?

```sql
SELECT * FROM orders WHERE status = 'paid' AND created_at > NOW() - INTERVAL '7 days';
```

**Решения:**
1. Убрать `SELECT *`, оставить нужные поля.
2. Добавить составной индекс:
   ```sql
   CREATE INDEX idx_orders_status_created ON orders(status, created_at);
   ```
3. Или частичный индекс:
   ```sql
   CREATE INDEX idx_orders_paid ON orders(created_at) WHERE status = 'paid';
   ```
4. Проверить `EXPLAIN ANALYZE` — используется ли индекс.

### <a id="задача-2">Задача 2</a>
Найти проблему в запросе.

```sql
SELECT * FROM users WHERE LOWER(email) = 'ivan@example.com';
```

**Проблема:** функция `LOWER` мешает обычному индексу по `email`.

**Решение:** функциональный индекс.
```sql
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
```

### <a id="задача-3">Задача 3</a>
Прочитать план.

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id)
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.name;
```

**Что искать:**
- `Seq Scan` на `users` — нормально, если таблица небольшая.
- `Hash Left Join` — нормальный способ соединения.
- `actual rows` — должно быть близко к `rows`.

---

## <a id="8-чек-лист">8. Чек-лист</a>

- [ ] Понимаю порядок выполнения запроса
- [ ] Знаю, что такое индекс и когда он помогает
- [ ] Умею создавать составные и частичные индексы
- [ ] Читаю `EXPLAIN` / `EXPLAIN ANALYZE`
- [ ] Избегаю антипаттернов (`SELECT *`, функции на полях)
- [ ] Понимаю партиционирование
- [ ] Знаю, когда нужно `ANALYZE`
