# SQL: аналитика данных

## Содержание

1. Зачем аналитику продвинутая аналитика
2. Перцентили и медиана
3. Статистика: stddev, variance
4. Когортный анализ
5. Retention
6. Воронки
7. RFM-анализ
8. ABC-анализ
9. Скользящие средние
10. Практика
11. Чек-лист

---

## 1. Зачем аналитику продвинутая аналитика

Базовых агрегатов (`SUM`, `COUNT`, `AVG`) хватает для простых отчётов. Но бизнес спрашивает:

- «Какая медиана чека?» — `AVG` врёт при выбросах.
- «Сколько клиентов вернулось?» — retention.
- «Какие клиенты лучшие?» — RFM.
- «Есть ли сезонность?» — скользящее среднее.
- «Где отваливаются пользователи?» — воронка.

Аналитик должен уметь это считать SQL-ом.

---

## 2. Перцентили и медиана

### Медиана (P50)

```sql
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total) AS median,
    AVG(total) AS mean
FROM orders;
```

**Разница:** при выбросах `AVG` сильно завышен, `MEDIAN` устойчив.

### Другие перцентили

```sql
SELECT
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY total) AS p25,
    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY total) AS p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY total) AS p75,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY total) AS p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY total) AS p99
FROM orders
WHERE status = 'paid';
```

**Зачем:** P95/P99 показывают «хвосты» — медленные запросы, дорогие заказы, долгие доставки.

### PERCENTILE_CONT vs PERCENTILE_DISC

- `CONT` — интерполирует (может вернуть значение, которого нет в данных).
- `DISC` — берёт ближайшее реальное.

### PERCENT_RANK — позиция в распределении

```sql
SELECT
    order_id,
    total,
    ROUND(PERCENT_RANK() OVER (ORDER BY total) * 100, 2) AS pct_rank
FROM orders;
```

### NTILE — разбить на группы

```sql
SELECT
    user_id,
    SUM(total) AS revenue,
    NTILE(4) OVER (ORDER BY SUM(total) DESC) AS quartile
FROM orders
GROUP BY user_id;
```

**Зачем:** разделить клиентов на 4 группы по выручке (топ-25%, средние, слабые).

---

## 3. Статистика: stddev, variance

```sql
SELECT
    AVG(total)                              AS mean,
    STDDEV(total)                           AS stddev,
    VARIANCE(total)                         AS variance,
    MIN(total)                              AS min,
    MAX(total)                              AS max,
    MAX(total) - MIN(total)                 AS spread
FROM orders;
```

### Коэффициент вариации

```sql
SELECT
    STDDEV(total) / NULLIF(AVG(total), 0) AS cv
FROM orders;
```

**Интерпретация:**
- `cv < 0.3` — стабильные заказы;
- `cv > 1` — высокая вариативность.

### MODE — самое частое значение

```sql
SELECT MODE() WITHIN GROUP (ORDER BY status) AS most_common_status
FROM orders;
```

---

## 4. Когортный анализ

**Когорта** — группа пользователей с общим признаком (например, месяц первой покупки).

```sql
WITH first_order AS (
    SELECT
        user_id,
        DATE_TRUNC('month', MIN(created_at)) AS cohort_month
    FROM orders
    GROUP BY user_id
),
activity AS (
    SELECT
        o.user_id,
        f.cohort_month,
        DATE_TRUNC('month', o.created_at) AS activity_month
    FROM orders o
    JOIN first_order f ON o.user_id = f.user_id
)
SELECT
    cohort_month,
    activity_month,
    COUNT(DISTINCT user_id) AS users
FROM activity
GROUP BY cohort_month, activity_month
ORDER BY cohort_month, activity_month;
```

### Сдвиг: номер месяца жизни когорты

```sql
WITH first_order AS (
    SELECT user_id, DATE_TRUNC('month', MIN(created_at)) AS cohort_month
    FROM orders GROUP BY user_id
),
activity AS (
    SELECT
        o.user_id,
        f.cohort_month,
        DATE_TRUNC('month', o.created_at) AS activity_month
    FROM orders o
    JOIN first_order f ON o.user_id = f.user_id
)
SELECT
    cohort_month,
    (EXTRACT(YEAR  FROM activity_month) - EXTRACT(YEAR  FROM cohort_month)) * 12
    + (EXTRACT(MONTH FROM activity_month) - EXTRACT(MONTH FROM cohort_month))
        AS month_number,
    COUNT(DISTINCT user_id) AS users
FROM activity
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;
```

**Результат:** таблица «когорта × месяц жизни → количество активных».

---

## 5. Retention

### D1 / D7 / D30

```sql
WITH first_visit AS (
    SELECT user_id, MIN(DATE(created_at)) AS first_day
    FROM events
    GROUP BY user_id
)
SELECT
    fv.first_day AS cohort_day,
    COUNT(DISTINCT fv.user_id) AS new_users,
    COUNT(DISTINCT CASE WHEN DATE(e.created_at) = fv.first_day + 1  THEN e.user_id END) AS d1,
    COUNT(DISTINCT CASE WHEN DATE(e.created_at) = fv.first_day + 7  THEN e.user_id END) AS d7,
    COUNT(DISTINCT CASE WHEN DATE(e.created_at) = fv.first_day + 30 THEN e.user_id END) AS d30
FROM first_visit fv
LEFT JOIN events e ON e.user_id = fv.user_id
GROUP BY fv.first_day
ORDER BY fv.first_day;
```

### Retention rate

```sql
WITH first_visit AS (
    SELECT user_id, MIN(DATE(created_at)) AS first_day
    FROM events GROUP BY user_id
),
activity AS (
    SELECT DISTINCT user_id, DATE(created_at) AS day FROM events
)
SELECT
    fv.first_day,
    COUNT(DISTINCT fv.user_id) AS cohort_size,
    COUNT(DISTINCT CASE WHEN a.day = fv.first_day + 7 THEN a.user_id END) AS d7_users,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN a.day = fv.first_day + 7 THEN a.user_id END)
        / NULLIF(COUNT(DISTINCT fv.user_id), 0),
        2
    ) AS d7_rate
FROM first_visit fv
LEFT JOIN activity a ON fv.user_id = a.user_id
GROUP BY fv.first_day
ORDER BY fv.first_day;
```

---

## 6. Воронки

```sql
WITH events_by_user AS (
    SELECT
        user_id,
        MAX(CASE WHEN event = 'visit'    THEN 1 ELSE 0 END) AS visited,
        MAX(CASE WHEN event = 'signup'   THEN 1 ELSE 0 END) AS signed,
        MAX(CASE WHEN event = 'add_cart' THEN 1 ELSE 0 END) AS added,
        MAX(CASE WHEN event = 'purchase' THEN 1 ELSE 0 END) AS purchased
    FROM events
    WHERE created_at >= '2026-01-01'
    GROUP BY user_id
)
SELECT
    SUM(visited)   AS step1_visit,
    SUM(signed)    AS step2_signup,
    SUM(added)     AS step3_cart,
    SUM(purchased) AS step4_purchase,
    ROUND(100.0 * SUM(signed)    / NULLIF(SUM(visited), 0), 2) AS conv_1_2,
    ROUND(100.0 * SUM(added)     / NULLIF(SUM(signed), 0),  2) AS conv_2_3,
    ROUND(100.0 * SUM(purchased) / NULLIF(SUM(added), 0),   2) AS conv_3_4
FROM events_by_user;
```

---

## 7. RFM-анализ

**R**ecency, **F**requency, **M**onetary — сегментация клиентов.

```sql
WITH rfm AS (
    SELECT
        user_id,
        MAX(created_at)::date                       AS last_order,
        (CURRENT_DATE - MAX(created_at)::date)      AS recency,
        COUNT(*)                                    AS frequency,
        SUM(total)                                  AS monetary
    FROM orders
    WHERE status = 'paid'
    GROUP BY user_id
),
scored AS (
    SELECT
        user_id,
        recency, frequency, monetary,
        NTILE(5) OVER (ORDER BY recency DESC)   AS r_score,  -- 5 = давно
        NTILE(5) OVER (ORDER BY frequency)      AS f_score,
        NTILE(5) OVER (ORDER BY monetary)       AS m_score
    FROM rfm
)
SELECT
    user_id,
    recency, frequency, monetary,
    r_score, f_score, m_score,
    r_score + f_score + m_score AS rfm_total,
    CASE
        WHEN r_score + f_score + m_score >= 13 THEN 'VIP'
        WHEN r_score + f_score + m_score >= 9  THEN 'loyal'
        WHEN r_score + f_score + m_score >= 6  THEN 'regular'
        ELSE 'at_risk'
    END AS segment
FROM scored
ORDER BY rfm_total DESC;
```

---

## 8. ABC-анализ

Разделение товаров/клиентов по вкладу в выручку.

```sql
WITH revenue AS (
    SELECT
        product_id,
        SUM(total) AS revenue
    FROM order_items oi
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status = 'paid'
    GROUP BY product_id
),
cumulative AS (
    SELECT
        product_id,
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC) AS cum_revenue,
        SUM(revenue) OVER ()                       AS total_revenue
    FROM revenue
)
SELECT
    product_id,
    revenue,
    ROUND(100.0 * cum_revenue / total_revenue, 2) AS cum_pct,
    CASE
        WHEN 100.0 * cum_revenue / total_revenue <= 80 THEN 'A'
        WHEN 100.0 * cum_revenue / total_revenue <= 95 THEN 'B'
        ELSE 'C'
    END AS abc_class
FROM cumulative
ORDER BY revenue DESC;
```

---

## 9. Скользящие средние

### Скользящее среднее за 7 дней

```sql
WITH daily AS (
    SELECT DATE(created_at) AS day, SUM(total) AS revenue
    FROM orders
    WHERE status = 'paid'
    GROUP BY DATE(created_at)
)
SELECT
    day,
    revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 2
    ) AS moving_avg_7d
FROM daily
ORDER BY day;
```

### Накопительная сумма

```sql
SELECT
    day,
    revenue,
    SUM(revenue) OVER (ORDER BY day) AS cumulative
FROM daily;
```

### Сравнение с прошлой неделей

```sql
SELECT
    day,
    revenue,
    LAG(revenue, 7) OVER (ORDER BY day)                    AS prev_week,
    revenue - LAG(revenue, 7) OVER (ORDER BY day)          AS wow_diff
FROM daily;
```

---

## 10. Практика

### Задача 1
Медиана и P95 доставки по регионам.

```sql
SELECT
    region,
    PERCENTILE_CONT(0.5)  WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (delivered_at - created_at)) / 3600) AS median_hours,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (delivered_at - created_at)) / 3600) AS p95_hours
FROM orders
WHERE delivered_at IS NOT NULL
GROUP BY region;
```

### Задача 2
Топ-10% клиентов по выручке.

```sql
WITH users_revenue AS (
    SELECT user_id, SUM(total) AS revenue
    FROM orders WHERE status = 'paid'
    GROUP BY user_id
),
ranked AS (
    SELECT
        user_id, revenue,
        PERCENT_RANK() OVER (ORDER BY revenue) AS pct_rank
    FROM users_revenue
)
SELECT * FROM ranked WHERE pct_rank >= 0.9
ORDER BY revenue DESC;
```

### Задача 3
Retention по когортам в виде матрицы.

```sql
WITH first_visit AS (
    SELECT user_id, DATE_TRUNC('week', MIN(created_at)) AS cohort_week
    FROM events GROUP BY user_id
),
activity AS (
    SELECT DISTINCT
        e.user_id,
        f.cohort_week,
        DATE_TRUNC('week', e.created_at) AS activity_week
    FROM events e
    JOIN first_visit f ON e.user_id = f.user_id
)
SELECT
    cohort_week,
    EXTRACT(EPOCH FROM (activity_week - cohort_week)) / 604800 AS week_number,
    COUNT(DISTINCT user_id) AS users
FROM activity
GROUP BY cohort_week, week_number
ORDER BY cohort_week, week_number;
```

---

## 11. Чек-лист

- [ ] Считаю медиану и перцентили через `PERCENTILE_CONT`
- [ ] Знаю `STDDEV`, `VARIANCE`, `MODE`
- [ ] Строю когортный анализ
- [ ] Считаю retention (D1, D7, D30)
- [ ] Строю воронки конверсии
- [ ] Делаю RFM-сегментацию
- [ ] Делаю ABC-анализ
- [ ] Считаю скользящие средние и накопительные суммы
