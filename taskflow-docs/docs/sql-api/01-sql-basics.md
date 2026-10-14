# <a id="sql-базовый-уровень">SQL: Базовый уровень</a>

## <a id="содержание">Содержание</a>
1. Что такое SQL
2. SELECT — выборка данных
3. WHERE — фильтрация
4. ORDER BY — сортировка
5. LIMIT / OFFSET — ограничение
6. DISTINCT — уникальные значения
7. Операторы и типы данных
8. Практика

---

## <a id="1-что-такое-sql">1. Что такое SQL</a>

**SQL (Structured Query Language)** — декларативный язык запросов к реляционным базам данных. Аналитик пишет запрос, СУБД решает, как его выполнить.

**Популярные СУБД:**
| СУБД | Особенности |
|---|---|
| PostgreSQL | Open-source, мощная, стандарт де-факто |
| MySQL | Популярна в вебе |
| MS SQL Server | Enterprise, Microsoft |
| Oracle | Банки, крупный enterprise |
| SQLite | Встроенная, для прототипов |

**Синтаксис в целом одинаковый**, различия — в деталях (функции работы с датами, строками).

---

## <a id="2-select-выборка-данных">2. SELECT — выборка данных</a>

Базовый запрос:

```sql
SELECT column1, column2
FROM table_name;
```

**Пример:**
```sql
SELECT id, name, email
FROM users;
```

**Псевдонимы (алиасы):**
```sql
SELECT
  id AS user_id,
  name AS full_name,
  email
FROM users;
```

**Все колонки (использовать осторожно):**
```sql
SELECT * FROM users;
```

**Зачем аналитику:** посмотреть, какие данные вообще есть в таблице, какие поля заполнены, какие значения принимают.

---

## <a id="3-where-фильтрация">3. WHERE — фильтрация</a>

```sql
SELECT *
FROM users
WHERE status = 'active';
```

### <a id="основные-операторы">Основные операторы</a>

| Оператор | Пример | Что делает |
|---|---|---|
| `=` | `WHERE status = 'active'` | Равно |
| `<>` / `!=` | `WHERE status <> 'deleted'` | Не равно |
| `>` `<` `>=` `<=` | `WHERE age >= 18` | Сравнение |
| `BETWEEN` | `WHERE age BETWEEN 18 AND 65` | Диапазон (включительно) |
| `IN` | `WHERE status IN ('active', 'pending')` | Вхождение в список |
| `NOT IN` | `WHERE id NOT IN (1, 2, 3)` | Исключение |
| `LIKE` | `WHERE name LIKE 'Ив%'` | Шаблон (`%` — любые символы, `_` — один символ) |
| `IS NULL` | `WHERE phone IS NULL` | Пустые значения |
| `IS NOT NULL` | `WHERE phone IS NOT NULL` | Заполненные значения |

### <a id="логические-операторы">Логические операторы</a>

```sql
SELECT *
FROM orders
WHERE status = 'paid'
  AND amount > 1000
  AND created_at >= '2026-01-01';
```

```sql
SELECT *
FROM users
WHERE country = 'RU' OR country = 'KZ';
```

### <a id="скобки-для-приоритета">Скобки для приоритета</a>

```sql
SELECT *
FROM orders
WHERE (status = 'paid' OR status = 'shipped')
  AND amount > 500;
```

⚠️ **Важно:** `NOT IN` с NULL возвращает пустой результат. Если в подзапросе возможны NULL — используйте `NOT EXISTS`.

---

## <a id="4-order-by-сортировка">4. ORDER BY — сортировка</a>

```sql
SELECT name, created_at
FROM users
ORDER BY created_at DESC;
```

- `ASC` — по возрастанию (по умолчанию).
- `DESC` — по убыванию.

**Сортировка по нескольким полям:**
```sql
SELECT name, city, age
FROM users
ORDER BY city ASC, age DESC;
```

**NULL в сортировке:**
- PostgreSQL: `NULLS LAST` / `NULLS FIRST`
```sql
ORDER BY phone NULLS LAST;
```

---

## <a id="5-limit-offset-ограничение">5. LIMIT / OFFSET — ограничение</a>

```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 10;
```

**С пропуском (пагинация):**
```sql
SELECT *
FROM orders
ORDER BY created_at DESC
LIMIT 10 OFFSET 20;
```

**В MS SQL:** `SELECT TOP 10 ...` вместо `LIMIT`.

---

## <a id="6-distinct-уникальные-значения">6. DISTINCT — уникальные значения</a>

```sql
SELECT DISTINCT country
FROM users;
```

**По нескольким полям:**
```sql
SELECT DISTINCT city, country
FROM users;
```

⚠️ `DISTINCT` работает по всей строке, а не по одному полю.

---

## <a id="7-операторы-и-типы-данных">7. Операторы и типы данных</a>

### <a id="основные-типы-данных">Основные типы данных</a>

| Тип | Пример | Где использовать |
|---|---|---|
| `INT` / `BIGINT` | 12345 | ID, счётчики |
| `VARCHAR(n)` / `TEXT` | 'Иван' | Строки |
| `BOOLEAN` | TRUE / FALSE | Флаги |
| `DATE` | '2026-01-15' | Дата |
| `TIMESTAMP` | '2026-01-15 10:30:00' | Дата+время |
| `NUMERIC` / `DECIMAL` | 1234.56 | Деньги |
| `JSON` / `JSONB` | '{"key": "value"}' | Гибкие структуры |

### <a id="приведение-типов">Приведение типов</a>

```sql
SELECT CAST('123' AS INT);
SELECT '123'::INT;  -- PostgreSQL
```

### <a id="работа-со-строками">Работа со строками</a>

```sql
SELECT LOWER(email), UPPER(name) FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;
SELECT LENGTH(name) FROM users;
```

### <a id="работа-с-датами">Работа с датами</a>

```sql
SELECT NOW();
SELECT CURRENT_DATE;
SELECT EXTRACT(YEAR FROM created_at) FROM orders;
SELECT DATE_TRUNC('month', created_at) FROM orders;
```

---

### <a id="coalesce-и-nullif">COALESCE и NULLIF</a>

Значения в колонках часто пустые (`NULL`), а сравнение с `NULL` даёт не `TRUE`/`FALSE`,
а снова `NULL`. Две функции закрывают почти все задачи по обработке пустых значений:

| Функция | Что делает | Пример |
|---|---|---|
| `COALESCE(a, b, ...)` | Первый из аргументов, который не `NULL` | `COALESCE(phone, 'не указан')` |
| `NULLIF(a, b)` | `NULL`, если `a = b`, иначе `a` | `NULLIF(qty, 0)` |

```sql
SELECT COALESCE(phone, 'не указан') AS contact FROM users;

-- деление на ноль: 0 → NULL, запрос не упадёт
SELECT revenue / NULLIF(orders_count, 0) AS avg_order FROM report;
```

**Ловушка:** аргументы `COALESCE` должны быть одного типа — иначе СУБД вернёт ошибку
приведения. А `NULLIF` часто используется внутри `COALESCE`: `COALESCE(NULLIF(a, b), c)`.

## <a id="8-практика">8. Практика</a>

### <a id="задача-1">Задача 1</a>
Найти всех активных пользователей из России, зарегистрированных в 2026 году, отсортировать по дате регистрации.

```sql
SELECT id, name, email, registration_date
FROM users
WHERE status = 'active'
  AND country = 'RU'
  AND registration_date >= '2026-01-01'
  AND registration_date < '2027-01-01'
ORDER BY registration_date DESC;
```

### <a id="задача-2">Задача 2</a>
Найти топ-5 самых дорогих оплаченных заказов.

```sql
SELECT order_id, user_id, amount, created_at
FROM orders
WHERE status = 'paid'
ORDER BY amount DESC
LIMIT 5;
```

### <a id="задача-3">Задача 3</a>
Найти пользователей без указанного телефона.

```sql
SELECT id, name, email
FROM users
WHERE phone IS NULL;
```

---

## <a id="чек-лист">Чек-лист</a>

- [ ] Пишу SELECT с нужными полями и алиасами
- [ ] Фильтрую через WHERE с `=`, `IN`, `BETWEEN`, `LIKE`, `IS NULL`
- [ ] Использую логические `AND`, `OR` со скобками
- [ ] Сортирую через ORDER BY (ASC/DESC, NULLS LAST)
- [ ] Ограничиваю LIMIT / OFFSET
- [ ] Понимаю типы данных и умею приводить типы
- [ ] Работаю со строками и датами
