# SQL: Базовый уровень

## Содержание
1. Что такое SQL
2. SELECT — выборка данных
3. WHERE — фильтрация
4. ORDER BY — сортировка
5. LIMIT / OFFSET — ограничение
6. DISTINCT — уникальные значения
7. Операторы и типы данных
8. Практика

---

## 1. Что такое SQL

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

## 2. SELECT — выборка данных

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

## 3. WHERE — фильтрация

```sql
SELECT *
FROM users
WHERE status = 'active';
```

### Основные операторы

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

### Логические операторы

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

### Скобки для приоритета

```sql
SELECT *
FROM orders
WHERE (status = 'paid' OR status = 'shipped')
  AND amount > 500;
```

⚠️ **Важно:** `NOT IN` с NULL возвращает пустой результат. Если в подзапросе возможны NULL — используйте `NOT EXISTS`.

---

## 4. ORDER BY — сортировка

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

## 5. LIMIT / OFFSET — ограничение

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

## 6. DISTINCT — уникальные значения

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

## 7. Операторы и типы данных

### Основные типы данных

| Тип | Пример | Где использовать |
|---|---|---|
| `INT` / `BIGINT` | 12345 | ID, счётчики |
| `VARCHAR(n)` / `TEXT` | 'Иван' | Строки |
| `BOOLEAN` | TRUE / FALSE | Флаги |
| `DATE` | '2026-01-15' | Дата |
| `TIMESTAMP` | '2026-01-15 10:30:00' | Дата+время |
| `NUMERIC` / `DECIMAL` | 1234.56 | Деньги |
| `JSON` / `JSONB` | '{"key": "value"}' | Гибкие структуры |

### Приведение типов

```sql
SELECT CAST('123' AS INT);
SELECT '123'::INT;  -- PostgreSQL
```

### Работа со строками

```sql
SELECT LOWER(email), UPPER(name) FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;
SELECT LENGTH(name) FROM users;
```

### Работа с датами

```sql
SELECT NOW();
SELECT CURRENT_DATE;
SELECT EXTRACT(YEAR FROM created_at) FROM orders;
SELECT DATE_TRUNC('month', created_at) FROM orders;
```

---

## 8. Практика

### Задача 1
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

### Задача 2
Найти топ-5 самых дорогих оплаченных заказов.

```sql
SELECT order_id, user_id, amount, created_at
FROM orders
WHERE status = 'paid'
ORDER BY amount DESC
LIMIT 5;
```

### Задача 3
Найти пользователей без указанного телефона.

```sql
SELECT id, name, email
FROM users
WHERE phone IS NULL;
```

---

## Чек-лист

- [ ] Пишу SELECT с нужными полями и алиасами
- [ ] Фильтрую через WHERE с `=`, `IN`, `BETWEEN`, `LIKE`, `IS NULL`
- [ ] Использую логические `AND`, `OR` со скобками
- [ ] Сортирую через ORDER BY (ASC/DESC, NULLS LAST)
- [ ] Ограничиваю LIMIT / OFFSET
- [ ] Понимаю типы данных и умею приводить типы
- [ ] Работаю со строками и датами