# <a id="sql-диалекты-субд">SQL: диалекты СУБД</a>

## <a id="содержание">Содержание</a>

1. Зачем аналитику знать диалекты
2. Сравнительная таблица
3. Ограничение строк (LIMIT / TOP / ROWNUM)
4. Работа со строками
5. Работа с датами
6. Работа с NULL
7. UPSERT
8. Оконные функции
9. JSON
10. Чек-лист

---

## <a id="1-зачем-аналитику-знать-диалекты">1. Зачем аналитику знать диалекты</a>

SQL — стандарт, но каждая СУБД добавляет своё. Аналитик переходит между проектами, где PostgreSQL, MySQL, MS SQL, Oracle. Один и тот же запрос может не работать.

**Типовая ситуация:** вы написали запрос в PostgreSQL, а в продакшене — MS SQL. `LIMIT` там не работает.

---

## <a id="2-сравнительная-таблица">2. Сравнительная таблица</a>

| Возможность | PostgreSQL | MySQL | MS SQL | Oracle |
|---|---|---|---|---|
| Ограничение строк | `LIMIT n` | `LIMIT n` | `TOP n` | `FETCH FIRST n ROWS ONLY` |
| Строковые функции | `\|\|` или `CONCAT` | `CONCAT` | `+` | `\|\|` |
| Текущая дата | `NOW()` | `NOW()` | `GETDATE()` | `SYSDATE` |
| Строковый тип | `TEXT` | `VARCHAR` до 65k | `NVARCHAR(MAX)` | `VARCHAR2`, `CLOB` |
| Автоинкремент | `SERIAL` / `IDENTITY` | `AUTO_INCREMENT` | `IDENTITY` | `SEQUENCE` |
| UPSERT | `ON CONFLICT` | `ON DUPLICATE KEY` | `MERGE` | `MERGE` |
| Булев тип | `BOOLEAN` | `TINYINT(1)` | `BIT` | ❌ (NUMBER(1)) |
| JSON | `JSONB` | `JSON` | `NVARCHAR` + функции | `JSON` (12c+) |
| Схема по умолчанию | `public` | нет | `dbo` | `USER` |

---

## <a id="3-ограничение-строк">3. Ограничение строк</a>

### PostgreSQL / MySQL

```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10 OFFSET 20;
```

### MS SQL

```sql
SELECT TOP 10 * FROM orders ORDER BY created_at DESC;

-- начиная с SQL Server 2012
SELECT * FROM orders
ORDER BY created_at DESC
OFFSET 20 ROWS FETCH NEXT 10 ROWS ONLY;
```

### Oracle

```sql
SELECT * FROM orders
ORDER BY created_at DESC
FETCH FIRST 10 ROWS ONLY;

-- старый вариант (до 12c)
SELECT * FROM (
    SELECT * FROM orders ORDER BY created_at DESC
) WHERE ROWNUM <= 10;
```

---

## <a id="4-работа-со-строками">4. Работа со строками</a>

### <a id="конкатенация">Конкатенация</a>

```sql
-- PostgreSQL / Oracle
SELECT first_name || ' ' || last_name FROM users;

-- MySQL / PostgreSQL
SELECT CONCAT(first_name, ' ', last_name) FROM users;

-- MS SQL
SELECT first_name + ' ' + last_name FROM users;
```

### <a id="длина-строки">Длина строки</a>

```sql
-- PostgreSQL / MySQL
SELECT LENGTH(name);

-- MS SQL / Oracle
SELECT LEN(name) FROM users;
```

### <a id="поиск-подстроки">Поиск подстроки</a>

```sql
-- PostgreSQL
SELECT POSITION('@' IN email) FROM users;

-- MySQL
SELECT LOCATE('@', email) FROM users;

-- MS SQL
SELECT CHARINDEX('@', email) FROM users;
```

### <a id="регистр">Регистр</a>

```sql
-- везде
SELECT LOWER(email), UPPER(name);
```

### <a id="регистронезависимый-like">Регистронезависимый LIKE</a>

```sql
-- PostgreSQL
WHERE email ILIKE '%gmail%'

-- MySQL (по умолчанию case-insensitive)
WHERE email LIKE '%gmail%'

-- MS SQL (зависит от collation)
WHERE email LIKE '%gmail%' COLLATE SQL_Latin1_General_CP1_CI_AS
```

---

## <a id="5-работа-с-датами">5. Работа с датами</a>

### <a id="текущее-время">Текущее время</a>

| СУБД | Функция |
|---|---|
| PostgreSQL | `NOW()`, `CURRENT_TIMESTAMP` |
| MySQL | `NOW()`, `CURRENT_TIMESTAMP` |
| MS SQL | `GETDATE()`, `SYSDATETIME()` |
| Oracle | `SYSDATE`, `SYSTIMESTAMP` |

### <a id="усечение">Усечение</a>

```sql
-- PostgreSQL
SELECT DATE_TRUNC('month', created_at) FROM orders;

-- MySQL
SELECT DATE_FORMAT(created_at, '%Y-%m-01') FROM orders;

-- MS SQL
SELECT DATEFROMPARTS(YEAR(created_at), MONTH(created_at), 1) FROM orders;

-- Oracle
SELECT TRUNC(created_at, 'MM') FROM orders;
```

### <a id="разница-между-датами">Разница между датами</a>

```sql
-- PostgreSQL
SELECT delivered_at - created_at FROM orders;

-- MySQL
SELECT TIMESTAMPDIFF(HOUR, created_at, delivered_at) FROM orders;

-- MS SQL
SELECT DATEDIFF(HOUR, created_at, delivered_at) FROM orders;

-- Oracle
SELECT (delivered_at - created_at) * 24 FROM orders;  -- в часах
```

---

## <a id="6-работа-с-null">6. Работа с NULL</a>

### <a id="coalesce-везде">COALESCE — везде</a>

```sql
SELECT COALESCE(phone, 'не указан') FROM users;
```

### <a id="аналоги">Аналоги</a>

| СУБД | Функция |
|---|---|
| PostgreSQL | `COALESCE`, `NULLIF` |
| MySQL | `COALESCE`, `IFNULL`, `NULLIF` |
| MS SQL | `COALESCE`, `ISNULL`, `NULLIF` |
| Oracle | `COALESCE`, `NVL`, `NULLIF` |

### <a id="проверка-null">Проверка NULL</a>

```sql
-- везде
WHERE phone IS NULL
WHERE phone IS NOT NULL
```

### <a id="условная-замена">Условная замена</a>

```sql
-- PostgreSQL / MySQL / MS SQL
SELECT CASE WHEN phone IS NULL THEN 'нет' ELSE phone END FROM users;

-- Oracle
SELECT NVL(phone, 'нет') FROM users;
```

---

## 7. UPSERT

### PostgreSQL

```sql
INSERT INTO orders (external_id, total)
VALUES ('MAG-001', 1000)
ON CONFLICT (external_id)
DO UPDATE SET total = EXCLUDED.total;
```

### MySQL

```sql
INSERT INTO orders (external_id, total)
VALUES ('MAG-001', 1000)
ON DUPLICATE KEY UPDATE total = VALUES(total);
```

### MS SQL / Oracle

```sql
MERGE INTO orders AS target
USING (SELECT 'MAG-001' AS external_id, 1000 AS total) AS src
ON target.external_id = src.external_id
WHEN MATCHED THEN UPDATE SET total = src.total
WHEN NOT MATCHED THEN INSERT (external_id, total) VALUES (src.external_id, src.total);
```

---

## <a id="8-оконные-функции">8. Оконные функции</a>

Оконные функции есть в PostgreSQL, MySQL 8+, MS SQL, Oracle. Синтаксис одинаковый:

```sql
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)
RANK()       OVER (ORDER BY revenue DESC)
LAG(total)   OVER (PARTITION BY user_id ORDER BY created_at)
SUM(total)   OVER (ORDER BY created_at)
```

⚠️ **В MySQL до 8.0 и старых версиях MariaDB** оконных функций нет. Используйте переменные или self-join.

---

## 9. JSON

### PostgreSQL (JSONB)

```sql
SELECT data->>'name' FROM events;
SELECT * FROM events WHERE data @> '{"type": "purchase"}';
SELECT JSONB_ARRAY_ELEMENTS(items) FROM orders;
```

### MySQL (JSON)

```sql
SELECT JSON_EXTRACT(data, '$.name') FROM events;
SELECT * FROM events WHERE JSON_EXTRACT(data, '$.type') = 'purchase';
```

### <a id="ms-sql-2">MS SQL</a>

```sql
SELECT JSON_VALUE(data, '$.name') FROM events;
```

### <a id="oracle-2">Oracle</a>

```sql
SELECT JSON_VALUE(data, '$.name') FROM events;
```

---

## <a id="10-чек-лист">10. Чек-лист</a>

- [ ] Знаю, как ограничивать строки в 4 СУБД
- [ ] Умею конкатенировать строки в разных диалектах
- [ ] Знаю функции работы с датами в каждой СУБД
- [ ] Понимаю разницу `COALESCE` и `ISNULL` / `NVL`
- [ ] Умею писать UPSERT / MERGE
- [ ] Знаю про оконные функции и их поддержку
- [ ] Умею работать с JSON в PostgreSQL и MySQL
