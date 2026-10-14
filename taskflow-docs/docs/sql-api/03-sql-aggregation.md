# <a id="sql-агрегация-и-группировка">SQL: Агрегация и группировка</a>

## <a id="содержание">Содержание</a>
1. Агрегатные функции
2. GROUP BY
3. HAVING
4. Порядок выполнения
5. GROUP BY + JOIN
6. Практика

---

## <a id="1-агрегатные-функции">1. Агрегатные функции</a>

| Функция | Что делает | Пример |
|---|---|---|
| `COUNT(*)` | Количество строк | `COUNT(*)` |
| `COUNT(col)` | Количество не-NULL | `COUNT(phone)` |
| `COUNT(DISTINCT col)` | Уникальных значений | `COUNT(DISTINCT user_id)` |
| `SUM(col)` | Сумма | `SUM(amount)` |
| `AVG(col)` | Среднее | `AVG(amount)` |
| `MIN(col)` | Минимум | `MIN(created_at)` |
| `MAX(col)` | Максимум | `MAX(amount)` |

### <a id="пример-без-группировки">Пример без группировки</a>

```sql
SELECT
  COUNT(*) AS total_orders,
  SUM(amount) AS total_revenue,
  AVG(amount) AS avg_check,
  MIN(amount) AS min_order,
  MAX(amount) AS max_order
FROM orders
WHERE status = 'paid';
```

**Результат — одна строка:**
| total_orders | total_revenue | avg_check | min_order | max_order |
|---|---|---|---|---|
| 1520 | 3850000 | 2532.89 | 100 | 98000 |

---

## 2. GROUP BY

Разбивает строки на группы и применяет агрегат к каждой.

```sql
SELECT status, COUNT(*) AS cnt
FROM orders
GROUP BY status;
```

**Результат:**
| status | cnt |
|---|---|
| paid | 1200 |
| pending | 250 |
| cancelled | 70 |

### <a id="правило">Правило</a>

В `SELECT` можно выводить **только**:
- поля из `GROUP BY`;
- агрегатные функции.

```sql
-- ❌ Ошибка: name не в GROUP BY и не агрегат
SELECT name, COUNT(*)
FROM users
GROUP BY country;
```

### <a id="группировка-по-нескольким-полям">Группировка по нескольким полям</a>

```sql
SELECT country, city, COUNT(*) AS users_count
FROM users
GROUP BY country, city
ORDER BY country, users_count DESC;
```

---

## 3. HAVING

Фильтр **после** группировки (в отличие от WHERE — до).

```sql
SELECT user_id, SUM(amount) AS total
FROM orders
GROUP BY user_id
HAVING SUM(amount) > 10000;
```

### WHERE vs HAVING

| | WHERE | HAVING |
|---|---|---|
| Когда применяется | До группировки | После группировки |
| К чему | К строкам | К группам |
| Агрегаты | ❌ | ✅ |

**Комбинированный пример:**
```sql
SELECT user_id, COUNT(*) AS orders_count, SUM(amount) AS total
FROM orders
WHERE created_at >= '2026-01-01'      -- фильтр строк
GROUP BY user_id
HAVING SUM(amount) > 5000              -- фильтр групп
ORDER BY total DESC;
```

---

## <a id="4-порядок-выполнения-запроса">4. Порядок выполнения запроса</a>

```
FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
```

Это объясняет:
- почему в `WHERE` нельзя использовать алиасы из `SELECT`;
- почему `HAVING` идёт после `GROUP BY`.

---

## 5. GROUP BY + JOIN

```sql
SELECT
  u.id,
  u.name,
  COUNT(o.id) AS orders_count,
  COALESCE(SUM(o.amount), 0) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY total_spent DESC;
```

**Важно:** `COALESCE` превращает NULL в 0 для пользователей без заказов.

---

### <a id="условная-агрегация">Условная агрегация</a>

`SUM(CASE WHEN ...)` — несколько метрик **одним запросом** вместо отдельных выборок
на каждую: именно так собирают сводные таблицы (pivot).

```sql
SELECT
  SUM(CASE WHEN status = 'paid'    THEN amount ELSE 0 END) AS paid_sum,
  SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) AS pending_sum,
  COUNT(CASE WHEN created_at >= '2026-01-01' THEN 1 END) AS new_orders
FROM orders;
```

**Важно:** в `SUM` без `ELSE 0` строки, не попавшие под условие, дадут `NULL`
и исказят (или не изменят) сумму. В `COUNT(CASE ... THEN 1 END)` `ELSE` не нужен —
`COUNT` считает только не-`NULL` значения.

## <a id="6-практика">6. Практика</a>

### <a id="задача-1">Задача 1</a>
Средний чек по месяцам.

```sql
SELECT
  DATE_TRUNC('month', created_at) AS month,
  COUNT(*) AS orders_count,
  AVG(amount) AS avg_check
FROM orders
WHERE status = 'paid'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;
```

### <a id="задача-2">Задача 2</a>
Топ-10 клиентов по сумме покупок за год.

```sql
SELECT
  u.id,
  u.name,
  SUM(o.amount) AS total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= '2026-01-01'
GROUP BY u.id, u.name
ORDER BY total DESC
LIMIT 10;
```

### <a id="задача-3">Задача 3</a>
Категории, в которых больше 100 товаров.

```sql
SELECT category_id, COUNT(*) AS products_count
FROM products
GROUP BY category_id
HAVING COUNT(*) > 100;
```

### <a id="задача-4">Задача 4</a>
Количество уникальных покупателей по странам.

```sql
SELECT u.country, COUNT(DISTINCT o.user_id) AS buyers
FROM orders o
JOIN users u ON o.user_id = u.id
GROUP BY u.country
ORDER BY buyers DESC;
```

---

## <a id="чек-лист">Чек-лист</a>

- [ ] Использую COUNT, SUM, AVG, MIN, MAX
- [ ] Понимаю разницу COUNT(*) и COUNT(col)
- [ ] Знаю про COUNT(DISTINCT)
- [ ] Пишу GROUP BY по одному и нескольким полям
- [ ] Различаю WHERE и HAVING
- [ ] Понимаю порядок выполнения
- [ ] Умею группировать с JOIN и обрабатывать NULL через COALESCE
