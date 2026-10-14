# <a id="sql-ddl-dml-транзакции-и-права-доступа">SQL: DDL, DML, транзакции и права доступа</a>

## <a id="содержание">Содержание</a>

1. Зачем аналитику DDL и DML
2. DDL — определение структуры
3. DML — работа с данными
4. Ограничения целостности
5. Транзакции и ACID
6. VIEW и MATERIALIZED VIEW
7. Хранимые процедуры и триггеры
8. Права доступа
9. Практика
10. Чек-лист

---

## <a id="1-зачем-аналитику-ddl-и-dml">1. Зачем аналитику DDL и DML</a>

Аналитик в основном читает данные (`SELECT`), но регулярно сталкивается с:

- **согласованием изменений схемы** — «добавить поле `external_id` в `orders`»;
- **подготовкой тестовых данных** — `INSERT`/`UPDATE`/`DELETE`;
- **проверкой ограничений** — почему заказ не создаётся;
- **обсуждением производительности** — зачем индекс;
- **разграничением доступа** — кому что можно.

Без понимания DDL/DML аналитик не сможет описать изменение схемы в ТЗ.

---

## 2. DDL — Data Definition Language

DDL изменяет **структуру** БД: таблицы, индексы, схемы.

### CREATE TABLE

```sql
CREATE TABLE orders (
    id           BIGSERIAL PRIMARY KEY,
    external_id  VARCHAR(64) NOT NULL UNIQUE,
    user_id      BIGINT NOT NULL REFERENCES users(id),
    status       VARCHAR(16) NOT NULL DEFAULT 'created',
    total        NUMERIC(10, 2) NOT NULL CHECK (total >= 0),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ
);
```

### <a id="типы-данных-и-их-выбор">Типы данных и их выбор</a>

| Тип | Когда использовать |
|---|---|
| `BIGSERIAL` / `BIGINT GENERATED` | Суррогатные ID |
| `VARCHAR(n)` | Строки с ограничением длины |
| `TEXT` | Длинные тексты без ограничения |
| `NUMERIC(p, s)` | Деньги (никогда `FLOAT`!) |
| `TIMESTAMPTZ` | События с часовым поясом |
| `BOOLEAN` | Флаги |
| `JSONB` | Гибкие структуры |
| `UUID` | Распределённые ID |

### ALTER TABLE

```sql
-- добавить поле
ALTER TABLE orders ADD COLUMN external_id VARCHAR(64);

-- сделать NOT NULL после заполнения
ALTER TABLE orders ALTER COLUMN external_id SET NOT NULL;

-- добавить уникальность
ALTER TABLE orders ADD CONSTRAINT uq_orders_external UNIQUE (external_id);

-- удалить поле
ALTER TABLE orders DROP COLUMN legacy_code;
```

**Важно для аналитика:** в ТЗ описывать не только «добавить поле», но и:
- тип;
- обязательность (`NOT NULL`);
- значение по умолчанию;
- уникальность;
- как заполнить существующие строки (миграция).

### CREATE INDEX

```sql
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE UNIQUE INDEX uq_orders_external ON orders(external_id);
```

Индекс ускоряет поиск, но замедляет вставку. Аналитик согласовывает индексы с DBA.

### DROP

```sql
DROP TABLE orders;              -- удалить таблицу
DROP TABLE IF EXISTS orders;    -- безопасно
DROP INDEX idx_orders_user_id;  -- удалить индекс
```

---

## 3. DML — Data Manipulation Language

DML работает с **данными** внутри таблиц.

### INSERT

```sql
-- одна строка
INSERT INTO users (name, email, status)
VALUES ('Иван', 'ivan@example.com', 'active');

-- несколько строк
INSERT INTO users (name, email, status)
VALUES
    ('Иван',  'ivan@example.com',  'active'),
    ('Мария', 'maria@example.com', 'active');

-- с возвратом id
INSERT INTO users (name, email)
VALUES ('Пётр', 'petr@example.com')
RETURNING id, created_at;
```

### UPDATE

```sql
-- ⚠️ БЕЗ WHERE обновит ВСЕ строки
UPDATE users SET status = 'blocked';

-- правильно
UPDATE users
SET status = 'blocked', updated_at = NOW()
WHERE last_login < '2025-01-01';
```

**Правило аналитика:** перед `UPDATE`/`DELETE` всегда делайте `SELECT` с тем же `WHERE` — проверьте, сколько строк затронете.

### DELETE

```sql
DELETE FROM orders WHERE status = 'cancelled' AND created_at < '2025-01-01';
```

### UPSERT (INSERT ... ON CONFLICT)

Ключевой паттерн для интеграций: если запись есть — обновить, если нет — создать.

```sql
INSERT INTO orders (external_id, user_id, total)
VALUES ('MAG-001', 123, 1990.00)
ON CONFLICT (external_id)
DO UPDATE SET
    total = EXCLUDED.total,
    updated_at = NOW();
```

**Где использовать:** синхронизация, идемпотентные операции, ETL.

### <a id="merge-в-postgresql-через-on-conflict-в-ms-sql-merge">MERGE (в PostgreSQL — через ON CONFLICT, в MS SQL — MERGE)</a>

```sql
-- MS SQL
MERGE orders AS target
USING (SELECT 'MAG-001' AS external_id, 123 AS user_id) AS src
ON target.external_id = src.external_id
WHEN MATCHED THEN UPDATE SET user_id = src.user_id
WHEN NOT MATCHED THEN INSERT (external_id, user_id) VALUES (src.external_id, src.user_id);
```

---

## <a id="4-ограничения-целостности">4. Ограничения целостности</a>

| Ограничение | Что гарантирует | Пример |
|---|---|---|
| `PRIMARY KEY` | Уникальность + NOT NULL | `id BIGSERIAL PRIMARY KEY` |
| `FOREIGN KEY` | Ссылка на другую таблицу | `user_id REFERENCES users(id)` |
| `UNIQUE` | Уникальность значения | `external_id UNIQUE` |
| `NOT NULL` | Обязательность | `status NOT NULL` |
| `CHECK` | Условие на значение | `CHECK (total >= 0)` |
| `DEFAULT` | Значение по умолчанию | `DEFAULT NOW()` |

### <a id="поведение-при-удалении-родителя">Поведение при удалении родителя</a>

```sql
-- запрещено удалять пользователя с заказами (по умолчанию)
user_id BIGINT REFERENCES users(id)

-- каскадное удаление
user_id BIGINT REFERENCES users(id) ON DELETE CASCADE

-- зануление ссылки
user_id BIGINT REFERENCES users(id) ON DELETE SET NULL
```

**В ТЗ аналитик обязан описать:** что происходит при удалении связанной записи.

---

## <a id="5-транзакции-и-acid">5. Транзакции и ACID</a>

**Транзакция** — набор операций, которые выполняются как одно целое.

```sql
BEGIN;

UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;

COMMIT;  -- зафиксировать
-- ROLLBACK;  -- откатить при ошибке
```

### ACID

| Свойство | Что означает |
|---|---|
| **Atomicity** | Всё или ничего |
| **Consistency** | БД переходит из одного валидного состояния в другое |
| **Isolation** | Параллельные транзакции не мешают друг другу |
| **Durability** | После COMMIT данные не потеряются |

### <a id="уровни-изоляции">Уровни изоляции</a>

| Уровень | Грязное чтение | Неповторяющееся чтение | Фантомы |
|---|---|---|---|
| `READ UNCOMMITTED` | ✅ возможно | ✅ | ✅ |
| `READ COMMITTED` (по умолчанию в PG) | ❌ | ✅ | ✅ |
| `REPEATABLE READ` | ❌ | ❌ | ✅ |
| `SERIALIZABLE` | ❌ | ❌ | ❌ |

**Зачем аналитику:** понимать, почему отчёт, построенный в параллельной транзакции, может дать неконсистентные данные.

### <a id="пример-проблемы">Пример проблемы</a>

```sql
-- Транзакция A видит промежуточное состояние транзакции B
BEGIN;
-- другая транзакция переводит деньги
SELECT SUM(balance) FROM accounts;  -- может показать «потерянные» деньги
COMMIT;
```

**Решение для отчётов:** читать с read-only реплики или использовать `SERIALIZABLE`.

---

## <a id="6-view-и-materialized-view">6. VIEW и MATERIALIZED VIEW</a>

### <a id="view-виртуальная-таблица">VIEW — виртуальная таблица</a>

```sql
CREATE VIEW active_users AS
SELECT id, name, email
FROM users
WHERE status = 'active';

SELECT * FROM active_users WHERE email LIKE '%@gmail.com';
```

**Плюсы:** переиспользование, безопасность (скрывает поля).
**Минусы:** выполняется каждый раз.

### <a id="materialized-view-кэшированный-результат">MATERIALIZED VIEW — кэшированный результат</a>

```sql
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT
    DATE_TRUNC('month', created_at) AS month,
    SUM(total) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY DATE_TRUNC('month', created_at);

-- обновление
REFRESH MATERIALIZED VIEW monthly_revenue;
```

**Где использовать:** тяжёлые отчёты, дашборды.

---

## <a id="7-хранимые-процедуры-и-триггеры">7. Хранимые процедуры и триггеры</a>

### PROCEDURE / FUNCTION

```sql
CREATE FUNCTION total_revenue(p_user_id BIGINT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN (SELECT COALESCE(SUM(total), 0)
            FROM orders
            WHERE user_id = p_user_id AND status = 'paid');
END;
$$ LANGUAGE plpgsql;

SELECT total_revenue(123);
```

**Зачем аналитику:** понимать, есть ли бизнес-логика на стороне БД — она может влиять на данные.

### TRIGGER

```sql
CREATE TRIGGER trg_orders_updated
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
```

**Риск для аналитика:** триггеры меняют данные незаметно — их нужно учитывать при анализе.

---

## <a id="8-права-доступа">8. Права доступа</a>

```sql
-- создать роль
CREATE ROLE analyst_readonly;

-- дать доступ на чтение
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_readonly;

-- только на конкретную таблицу
GRANT SELECT ON orders TO analyst_readonly;

-- забрать право
REVOKE SELECT ON orders FROM analyst_readonly;
```

**Типовая практика:**
- аналитики работают с **read-only репликами**;
- PII-поля (телефон, email, паспорт) маскируются через VIEW;
- запись — только через сервис, не напрямую.

**В ТЗ:** описать, какие роли и права нужны для новой фичи.

---

## <a id="9-практика">9. Практика</a>

### <a id="задача-1">Задача 1</a>
Добавить поле `external_id` в таблицу `orders`, заполнить существующие строки, сделать `NOT NULL` и `UNIQUE`.

```sql
-- 1. добавить nullable
ALTER TABLE orders ADD COLUMN external_id VARCHAR(64);

-- 2. заполнить (например, из id)
UPDATE orders SET external_id = 'LEGACY-' || id WHERE external_id IS NULL;

-- 3. сделать обязательным и уникальным
ALTER TABLE orders ALTER COLUMN external_id SET NOT NULL;
ALTER TABLE orders ADD CONSTRAINT uq_orders_external UNIQUE (external_id);
```

### <a id="задача-2">Задача 2</a>
Идемпотентная вставка заказа из внешней системы.

```sql
INSERT INTO orders (external_id, user_id, total, status)
VALUES ('MAG-001', 123, 1990.00, 'created')
ON CONFLICT (external_id) DO NOTHING;
```

### <a id="задача-3">Задача 3</a>
Проверить, что заказ и позиции создаются атомарно.

```sql
BEGIN;

WITH new_order AS (
    INSERT INTO orders (external_id, user_id, total)
    VALUES ('MAG-002', 123, 500.00)
    RETURNING id
)
INSERT INTO order_items (order_id, product_id, quantity)
SELECT id, 1, 2 FROM new_order;

COMMIT;
```

---

## <a id="10-чек-лист">10. Чек-лист</a>

- [ ] Понимаю разницу DDL и DML
- [ ] Умею писать `CREATE TABLE` с ограничениями
- [ ] Знаю типы данных и выбираю правильный
- [ ] Пишу `INSERT` / `UPDATE` / `DELETE` с `WHERE`
- [ ] Использую `UPSERT` для идемпотентности
- [ ] Понимаю `FOREIGN KEY` и поведение при удалении
- [ ] Знаю транзакции, `BEGIN` / `COMMIT` / `ROLLBACK`
- [ ] Понимаю уровни изоляции
- [ ] Различаю `VIEW` и `MATERIALIZED VIEW`
- [ ] Умею описывать права доступа
