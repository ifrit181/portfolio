# <a id="sql-join-объединение-таблиц">SQL: JOIN — объединение таблиц</a>

## <a id="содержание">Содержание</a>
1. Зачем нужны JOIN
2. Виды JOIN
3. INNER JOIN
4. LEFT JOIN
5. RIGHT JOIN
6. FULL JOIN
7. CROSS JOIN
8. SELF JOIN
9. Типичные ошибки
10. Практика

---

## <a id="1-зачем-нужны-join">1. Зачем нужны JOIN</a>

Данные в реляционных БД **нормализованы** — разбиты по таблицам, чтобы избежать дублирования.

**Пример:**
- `users` — пользователи
- `orders` — заказы (хранит `user_id`, а не имя)

Чтобы получить «имя клиента + его заказ» — нужен JOIN.

```
users                    orders
+----+-------+          +----+---------+--------+
| id | name  |          | id | user_id | amount |
+----+-------+          +----+---------+--------+
| 1  | Иван  |          | 10 | 1       | 500    |
| 2  | Мария |          | 11 | 1       | 300    |
| 3  | Олег  |          | 12 | 2       | 800    |
+----+-------+          +----+---------+--------+
```

---

## <a id="2-виды-join">2. Виды JOIN</a>

| Тип | Что возвращает |
|---|---|
| **INNER JOIN** | Только совпадающие строки |
| **LEFT JOIN** | Все строки из левой + совпадения из правой |
| **RIGHT JOIN** | Все строки из правой + совпадения из левой |
| **FULL JOIN** | Все строки из обеих таблиц |
| **CROSS JOIN** | Декартово произведение |
| **SELF JOIN** | JOIN таблицы с самой собой |

---

## 3. INNER JOIN

Возвращает только те строки, где есть совпадение в обеих таблицах.

```sql
SELECT u.name, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;
```

**Результат:**
| name | amount |
|---|---|
| Иван | 500 |
| Иван | 300 |
| Мария | 800 |

⚠️ Олег не попал — у него нет заказов.

**Ключевое слово `INNER` можно опустить:**
```sql
SELECT u.name, o.amount
FROM users u
JOIN orders o ON u.id = o.user_id;
```

---

## 4. LEFT JOIN

Возвращает **все строки из левой таблицы** + совпадения из правой. Если совпадений нет — NULL.

```sql
SELECT u.name, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
```

**Результат:**
| name | amount |
|---|---|
| Иван | 500 |
| Иван | 300 |
| Мария | 800 |
| Олег | NULL |

**Типичный кейс аналитика:** найти пользователей без заказов.
```sql
SELECT u.id, u.name
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;
```

---

## 5. RIGHT JOIN

Зеркальный LEFT JOIN. Возвращает все строки из правой таблицы.

```sql
SELECT u.name, o.amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;
```

На практике **используется редко** — обычно переписывают через LEFT JOIN, поменяв таблицы местами.

---

## 6. FULL JOIN

Возвращает все строки из обеих таблиц, где нет совпадения — NULL.

```sql
SELECT u.name, o.amount
FROM users u
FULL JOIN orders o ON u.id = o.user_id;
```

**Результат:**
| name | amount |
|---|---|
| Иван | 500 |
| Иван | 300 |
| Мария | 800 |
| Олег | NULL |
| NULL | 900 |  ← заказ без пользователя

**Кейс:** поиск «сиротских» записей с обеих сторон.

```sql
SELECT u.id, o.id
FROM users u
FULL JOIN orders o ON u.id = o.user_id
WHERE u.id IS NULL OR o.id IS NULL;
```

---

## 7. CROSS JOIN

Декартово произведение: каждая строка первой × каждая строка второй.

```sql
SELECT u.name, p.title
FROM users u
CROSS JOIN products p;
```

Используется редко, обычно для генерации комбинаций (например, все пользователи × все категории).

---

## 8. SELF JOIN

JOIN таблицы с самой собой. Нужен для иерархий (сотрудник → руководитель).

```sql
SELECT
  e.name AS employee,
  m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;
```

---

## <a id="9-join-нескольких-таблиц">9. JOIN нескольких таблиц</a>

```sql
SELECT
  u.name AS user_name,
  o.id AS order_id,
  p.title AS product_title,
  oi.quantity
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

---

## <a id="10-типичные-ошибки">10. Типичные ошибки</a>

| Ошибка | Последствие | Как избежать |
|---|---|---|
| Забыть `ON` | Декартово произведение | Всегда указывать условие |
| Использовать `INNER` вместо `LEFT` | Теряются строки | Проверять, нужны ли все строки слева |
| Дубли из-за одного-ко-многим | Раздувание выборки | Использовать `DISTINCT` или агрегаты |
| Сравнивать NULL через `=` | Пустой результат | Использовать `IS NULL` |
| Не указать алиасы | Нечитаемый запрос | `users u`, `orders o` |

### <a id="пример-ловушки-с-дублями">Пример ловушки с дублями</a>

```sql
-- Если у пользователя 3 заказа — он появится 3 раза
SELECT u.name, o.id
FROM users u
JOIN orders o ON u.id = o.user_id;
```

**Решение — агрегация:**
```sql
SELECT u.name, COUNT(o.id) AS orders_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
```

---

## <a id="11-практика">11. Практика</a>

### <a id="задача-1">Задача 1</a>
Вывести всех пользователей и количество их заказов (включая тех, у кого заказов нет).

```sql
SELECT u.id, u.name, COUNT(o.id) AS orders_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name
ORDER BY orders_count DESC;
```

### <a id="задача-2">Задача 2</a>
Найти заказы, у которых нет привязанного пользователя.

```sql
SELECT o.id, o.amount
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE u.id IS NULL;
```

### <a id="задача-3">Задача 3</a>
Вывести все пары «пользователь — товар» из его заказов.

```sql
SELECT DISTINCT u.name, p.title
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

---

## <a id="чек-лист">Чек-лист</a>

- [ ] Понимаю разницу между INNER и LEFT JOIN
- [ ] Умею находить «сиротские» записи через LEFT JOIN + IS NULL
- [ ] Знаю, когда использовать FULL JOIN
- [ ] Пишу SELF JOIN для иерархий
- [ ] Указываю алиасы для читаемости
- [ ] Проверяю запрос на дубли
- [ ] Понимаю влияние JOIN на количество строк
