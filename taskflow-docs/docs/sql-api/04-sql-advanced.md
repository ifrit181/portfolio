# <a id="sql-продвинутый-уровень">SQL: Продвинутый уровень</a>

## <a id="содержание">Содержание</a>
1. Подзапросы
2. CTE (WITH)
3. Оконные функции
4. UNION / UNION ALL
5. CASE
6. Практика

---

## <a id="1-подзапросы">1. Подзапросы</a>

Запрос внутри запроса.

### <a id="в-where">В WHERE</a>

```sql
SELECT name
FROM users
WHERE id IN (
  SELECT user_id FROM orders WHERE amount > 10000
);
```

### <a id="в-from">В FROM</a>

```sql
SELECT AVG(total) AS avg_user_total
FROM (
  SELECT user_id, SUM(amount) AS total
  FROM orders
  GROUP BY user_id
) AS user_totals;
```

### <a id="в-select-скалярный-подзапрос">В SELECT (скалярный подзапрос)</a>

```sql
SELECT
  u.name,
  (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS orders_count
FROM users u;
```

⚠️ Медленнее, чем JOIN — использовать осторожно.

### EXISTS / NOT EXISTS

```sql
SELECT u.name
FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

**NOT EXISTS** — безопаснее, чем `NOT IN` (корректно работает с NULL).

---

## 2. CTE (WITH)

Common Table Expression — именованный временный набор. Делает сложные запросы читаемыми.

```sql
WITH paid_orders AS (
  SELECT user_id, amount
  FROM orders
  WHERE status = 'paid'
),
user_totals AS (
  SELECT user_id, SUM(amount) AS total
  FROM paid_orders
  GROUP BY user_id
)
SELECT u.name, ut.total
FROM users u
JOIN user_totals ut ON u.id = ut.user_id
ORDER BY ut.total DESC;
```

**Преимущества:**
- читаемость;
- переиспользование внутри запроса;
- можно ссылаться на предыдущие CTE.

---

## <a id="3-оконные-функции">3. Оконные функции</a>

Агрегат **без сворачивания строк**. Работает через `OVER()`.

### <a id="синтаксис">Синтаксис</a>

```sql
function() OVER (
  PARTITION BY col1
  ORDER BY col2
  ROWS BETWEEN ...
)
```

### <a id="row-number-нумерация">ROW_NUMBER — нумерация</a>

```sql
SELECT
  user_id,
  amount,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY amount DESC) AS rn
FROM orders;
```

**Кейс:** последний заказ каждого пользователя.
```sql
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders
)
SELECT * FROM ranked WHERE rn = 1;
```

### <a id="rank-dense-rank">RANK / DENSE_RANK</a>

| Функция | Результат при равенстве |
|---|---|
| `ROW_NUMBER` | 1, 2, 3 (уникальные) |
| `RANK` | 1, 1, 3 (с пропусками) |
| `DENSE_RANK` | 1, 1, 2 (без пропусков) |

### SUM / AVG OVER

```sql
SELECT
  user_id,
  created_at,
  amount,
  SUM(amount) OVER (PARTITION BY user_id ORDER BY created_at) AS running_total
FROM orders;
```

**Running total** — накопительная сумма по каждому пользователю.

### <a id="lag-lead-соседние-строки">LAG / LEAD — соседние строки</a>

```sql
SELECT
  user_id,
  created_at,
  amount,
  LAG(amount) OVER (PARTITION BY user_id ORDER BY created_at) AS prev_amount,
  amount - LAG(amount) OVER (PARTITION BY user_id ORDER BY created_at) AS diff
FROM orders;
```

---

## 4. UNION / UNION ALL

Объединение результатов двух запросов.

| Оператор | Дубли |
|---|---|
| `UNION` | Удаляет |
| `UNION ALL` | Оставляет |

```sql
SELECT name FROM customers
UNION
SELECT name FROM suppliers;
```

**Требования:**
- одинаковое количество колонок;
- совместимые типы.

**UNION ALL быстрее** — не делает дедупликацию.

---

## 5. CASE

Условная логика в запросе.

```sql
SELECT
  id,
  amount,
  CASE
    WHEN amount < 1000 THEN 'small'
    WHEN amount < 10000 THEN 'medium'
    ELSE 'large'
  END AS size_category
FROM orders;
```

### <a id="pivot-через-case">Pivot через CASE</a>

```sql
SELECT
  user_id,
  SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END) AS paid_sum,
  SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END) AS pending_sum
FROM orders
GROUP BY user_id;
```

---

## <a id="6-практика">6. Практика</a>

### <a id="задача-1">Задача 1</a>
Для каждого пользователя — его последний заказ.

```sql
WITH ranked AS (
  SELECT
    o.*,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM orders o
)
SELECT user_id, id, amount, created_at
FROM ranked
WHERE rn = 1;
```

### <a id="задача-2">Задача 2</a>
Динамика выручки по дням с накоплением.

```sql
SELECT
  DATE(created_at) AS day,
  SUM(amount) AS daily,
  SUM(SUM(amount)) OVER (ORDER BY DATE(created_at)) AS cumulative
FROM orders
WHERE status = 'paid'
GROUP BY DATE(created_at)
ORDER BY day;
```

### <a id="задача-3">Задача 3</a>
Разница между текущим и предыдущим заказом пользователя.

```sql
SELECT
  user_id,
  created_at,
  amount,
  amount - LAG(amount) OVER (PARTITION BY user_id ORDER BY created_at) AS diff
FROM orders;
```

### <a id="задача-4">Задача 4</a>
Пользователи с покупками в 2025 ИЛИ 2026 (UNION).

```sql
SELECT user_id FROM orders WHERE created_at >= '2025-01-01' AND created_at < '2026-01-01'
UNION
SELECT user_id FROM orders WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01';
```

---

## <a id="чек-лист">Чек-лист</a>

- [ ] Пишу подзапросы в WHERE, FROM, SELECT
- [ ] Использую EXISTS / NOT EXISTS
- [ ] Строю CTE для читаемости
- [ ] Использую ROW_NUMBER, RANK, LAG, LEAD
- [ ] Знаю про PARTITION BY в оконных функциях
- [ ] Применяю UNION и UNION ALL
- [ ] Пишу CASE для условной логики
