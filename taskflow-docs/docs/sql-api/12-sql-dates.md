# SQL: даты, время и часовые пояса

## Содержание

1. Зачем аналитику работа с датами
2. Типы дат и времени
3. TIMESTAMP vs TIMESTAMPTZ
4. Функции работы с датами
5. Часовые пояса
6. Интервалы
7. Генерация дат
8. Типичные кейсы
9. Практика
10. Чек-лист

---

## 1. Зачем аналитику работа с датами

80% метрик — это временные ряды:
- выручка по дням;
- DAU / MAU;
- retention;
- среднее время доставки;
- конверсия по неделям.

Без уверенной работы с датами аналитик не сможет построить ни один отчёт.

---

## 2. Типы дат и времени

| Тип | Хранит | Пример |
|---|---|---|
| `DATE` | Только дату | `2026-10-14` |
| `TIME` | Только время | `14:30:00` |
| `TIMESTAMP` | Дату+время без TZ | `2026-10-14 14:30:00` |
| `TIMESTAMPTZ` | Дату+время с TZ | `2026-10-14 14:30:00+03` |
| `INTERVAL` | Промежуток | `'3 days'` |

**Правило:** для событий всегда `TIMESTAMPTZ`. Для «дня рождения» — `DATE`.

---

## 3. TIMESTAMP vs TIMESTAMPTZ

| | `TIMESTAMP` | `TIMESTAMPTZ` |
|---|---|---|
| Хранит TZ | ❌ | ✅ (в UTC) |
| Отображает | Как есть | В TZ сессии |
| Для чего | «Локальное» время | События |

**Проблема без TZ:**
- Сервер в UTC, клиент в МСК → отчёты «съезжают» на 3 часа.
- Пользователь из Владивостока видит «вчерашний» заказ.

**Решение:** всегда `TIMESTAMPTZ` для событий (создание, оплата, доставка).

---

## 4. Функции работы с датами

### Текущее время

```sql
SELECT NOW();              -- с TZ
SELECT CURRENT_DATE;       -- только дата
SELECT CURRENT_TIMESTAMP;  -- синоним NOW()
```

### Извлечение частей

```sql
SELECT
    EXTRACT(YEAR  FROM created_at) AS year,
    EXTRACT(MONTH FROM created_at) AS month,
    EXTRACT(DAY   FROM created_at) AS day,
    EXTRACT(HOUR  FROM created_at) AS hour,
    EXTRACT(DOW   FROM created_at) AS dow;  -- 0 = воскресенье

-- PostgreSQL-специфично
SELECT DATE_PART('year', created_at) FROM orders;
```

### Усечение до периода

```sql
SELECT
    DATE_TRUNC('day',   created_at) AS day,
    DATE_TRUNC('week',  created_at) AS week,
    DATE_TRUNC('month', created_at) AS month,
    DATE_TRUNC('year',  created_at) AS year
FROM orders;
```

**Ключевой приём для отчётов:**
```sql
SELECT
    DATE_TRUNC('month', created_at) AS month,
    SUM(total) AS revenue
FROM orders
WHERE status = 'paid'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;
```

### Форматирование

```sql
SELECT TO_CHAR(created_at, 'YYYY-MM-DD') FROM orders;
SELECT TO_CHAR(created_at, 'DD.MM.YYYY HH24:MI') FROM orders;
```

### Парсинг строк

```sql
SELECT TO_DATE('14.10.2026', 'DD.MM.YYYY');
SELECT TO_TIMESTAMP('2026-10-14 14:30', 'YYYY-MM-DD HH24:MI');
```

---

## 5. Часовые пояса

### AT TIME ZONE

```sql
-- привести к МСК
SELECT created_at AT TIME ZONE 'Europe/Moscow' FROM orders;

-- текущее время в МСК
SELECT NOW() AT TIME ZONE 'Europe/Moscow';
```

### Хранение и отображение

**PostgreSQL:** `TIMESTAMPTZ` хранит UTC, отображает в TZ сессии.

```sql
SET TIME ZONE 'Europe/Moscow';
SELECT NOW();  -- покажет с +03
```

**Совет аналитику:**
- хранить всё в UTC (`TIMESTAMPTZ`);
- конвертировать в TZ пользователя только при отображении;
- в ТЗ явно указывать: «время в UTC» или «в TZ пользователя».

### Типичная ошибка

```sql
-- ❌ неправильно: сравнение "локального" времени с UTC
SELECT * FROM orders WHERE created_at >= '2026-10-14';

-- ✅ правильно: явно указать TZ
SELECT * FROM orders
WHERE created_at >= '2026-10-14 00:00:00+03';
```

---

## 6. Интервалы

```sql
SELECT NOW() + INTERVAL '1 day';
SELECT NOW() - INTERVAL '3 hours';
SELECT NOW() - INTERVAL '7 days';
SELECT NOW() - INTERVAL '1 month';

-- комбинированные
SELECT NOW() - INTERVAL '1 year 2 months 3 days';
```

**Типичные запросы:**
```sql
-- за последние 7 дней
WHERE created_at >= NOW() - INTERVAL '7 days'

-- за прошлый месяц
WHERE created_at >= DATE_TRUNC('month', NOW() - INTERVAL '1 month')
  AND created_at <  DATE_TRUNC('month', NOW())

-- за текущий год
WHERE created_at >= DATE_TRUNC('year', NOW())
```

---

## 7. Генерация дат

### GENERATE_SERIES (PostgreSQL)

```sql
SELECT GENERATE_SERIES(
    '2026-01-01'::date,
    '2026-01-31'::date,
    '1 day'::interval
) AS day;
```

**Зачем:** построить отчёт, где есть все дни, даже если не было заказов.

```sql
WITH days AS (
    SELECT GENERATE_SERIES(
        '2026-01-01'::date,
        '2026-01-31'::date,
        '1 day'::interval
    )::date AS day
),
daily AS (
    SELECT DATE(created_at) AS day, SUM(total) AS revenue
    FROM orders
    WHERE created_at >= '2026-01-01'
      AND created_at <  '2026-02-01'
    GROUP BY DATE(created_at)
)
SELECT d.day, COALESCE(dl.revenue, 0) AS revenue
FROM days d
LEFT JOIN daily dl ON d.day = dl.day
ORDER BY d.day;
```

**Без этого** в отчёте будут «дыры» — пропущенные дни.

---

## 8. Типичные кейсы

### Кейс 1: разница между датами

```sql
SELECT
    order_id,
    created_at,
    delivered_at,
    delivered_at - created_at AS delivery_time,
    EXTRACT(EPOCH FROM (delivered_at - created_at)) / 3600 AS hours
FROM orders
WHERE delivered_at IS NOT NULL;
```

### Кейс 2: возраст

```sql
SELECT
    name,
    birth_date,
    AGE(NOW(), birth_date) AS age_interval,
    EXTRACT(YEAR FROM AGE(NOW(), birth_date)) AS age_years
FROM users;
```

### Кейс 3: сравнение с предыдущим периодом

```sql
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(total) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS prev_month,
    revenue - LAG(revenue) OVER (ORDER BY month) AS diff,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0),
        2
    ) AS growth_pct
FROM monthly
ORDER BY month;
```

### Кейс 4: воронка по дням

```sql
SELECT
    DATE_TRUNC('week', created_at) AS week,
    COUNT(*) FILTER (WHERE event = 'visit')   AS visits,
    COUNT(*) FILTER (WHERE event = 'signup')  AS signups,
    COUNT(*) FILTER (WHERE event = 'purchase') AS purchases
FROM events
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week;
```

### Кейс 5: рабочие дни vs выходные

```sql
SELECT
    CASE
        WHEN EXTRACT(DOW FROM created_at) IN (0, 6) THEN 'weekend'
        ELSE 'weekday'
    END AS day_type,
    COUNT(*) AS orders,
    AVG(total) AS avg_check
FROM orders
GROUP BY day_type;
```

---

## 9. Практика

### Задача 1
Выручка по месяцам за 2026 год с заполнением пустых месяцев нулями.

```sql
WITH months AS (
    SELECT GENERATE_SERIES(
        '2026-01-01'::date,
        '2026-12-01'::date,
        '1 month'::interval
    )::date AS month
),
revenue AS (
    SELECT DATE_TRUNC('month', created_at)::date AS month, SUM(total) AS revenue
    FROM orders
    WHERE status = 'paid' AND created_at >= '2026-01-01'
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT m.month, COALESCE(r.revenue, 0) AS revenue
FROM months m
LEFT JOIN revenue r ON m.month = r.month
ORDER BY m.month;
```

### Задача 2
Retention: сколько пользователей вернулось через 7 дней.

```sql
WITH first_visit AS (
    SELECT user_id, MIN(DATE(created_at)) AS first_day
    FROM events
    GROUP BY user_id
)
SELECT
    fv.first_day,
    COUNT(DISTINCT fv.user_id) AS new_users,
    COUNT(DISTINCT CASE
        WHEN DATE(e.created_at) = fv.first_day + 7 THEN e.user_id
    END) AS returned_d7
FROM first_visit fv
LEFT JOIN events e ON fv.user_id = e.user_id
GROUP BY fv.first_day
ORDER BY fv.first_day;
```

### Задача 3
Среднее время доставки по неделям.

```sql
SELECT
    DATE_TRUNC('week', created_at) AS week,
    AVG(EXTRACT(EPOCH FROM (delivered_at - created_at)) / 3600) AS avg_hours
FROM orders
WHERE delivered_at IS NOT NULL
  AND created_at >= NOW() - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week;
```

---

## 10. Чек-лист

- [ ] Знаю типы `DATE`, `TIMESTAMP`, `TIMESTAMPTZ`, `INTERVAL`
- [ ] Использую `TIMESTAMPTZ` для событий
- [ ] Умею `EXTRACT`, `DATE_TRUNC`, `TO_CHAR`
- [ ] Понимаю часовые пояса и `AT TIME ZONE`
- [ ] Работаю с интервалами
- [ ] Знаю `GENERATE_SERIES` для заполнения пропусков
- [ ] Считаю разницу между датами
- [ ] Строю retention и воронки
