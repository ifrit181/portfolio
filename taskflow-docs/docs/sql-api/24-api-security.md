# Безопасность API

## Содержание

1. Зачем аналитику безопасность
2. OWASP API Top 10
3. Аутентификация и авторизация
4. Работа с чувствительными данными
5. Защита от атак
6. Rate limiting
7. Аудит и логирование
8. Требования к API в ТЗ
9. Практика
10. Чек-лист

---

## 1. Зачем аналитику безопасность

Аналитик не отвечает за security, но обязан:
- не проектировать небезопасные API;
- описывать требования к защите;
- знать типовые уязвимости;
- согласовывать с security-командой.

---

## 2. OWASP API Top 10

| # | Уязвимость | Что это |
|---|---|---|
| 1 | Broken Object Level Authorization | Пользователь A получает данные пользователя B |
| 2 | Broken Authentication | Слабые токены, отсутствие проверки |
| 3 | Broken Object Property Level Authorization | Возвращаются лишние поля |
| 4 | Unrestricted Resource Consumption | Нет лимитов (DoS) |
| 5 | Broken Function Level Authorization | Пользователь вызывает admin-функции |
| 6 | Unrestricted Access to Sensitive Business Flows | Массовая скупка, брутфорс |
| 7 | SSRF | Сервер делает запросы куда угодно |
| 8 | Security Misconfiguration | Дефолтные пароли, debug |
| 9 | Improper Inventory Management | Старые версии, забытые endpoints |
| 10 | Unsafe Consumption of APIs | Доверие к стороннему API |

**Что должен знать аналитик:** базово все 10, особенно 1, 2, 5.

---

## 3. Аутентификация и авторизация

### Аутентификация

- Токены с ограниченным сроком.
- Refresh-токены.
- MFA для критичных операций.

### Авторизация

- **RBAC** — по ролям (`admin`, `manager`, `user`).
- **ABAC** — по атрибутам (регион, отдел).
- **Проверка владения** — объект принадлежит пользователю.

```http
GET /api/v1/orders/456
Authorization: Bearer <token>

# Сервер должен проверить:
# - токен валиден;
# - user_id в токене == order.user_id
```

**Типовая ошибка:** проверять только токен, но не владение объектом (BOLA/IDOR).

---

## 4. Работа с чувствительными данными

### Классификация

| Уровень | Пример | Что делать |
|---|---|---|
| Public | Каталог | Без ограничений |
| Internal | ID заказов | Только авторизованным |
| Confidential | Email, телефон | Маскировать в логах |
| Restricted | Пароли, карты | Не хранить, не логировать |

### Маскирование

```json
{ "card": "**** **** **** 1234", "phone": "+7 *** *** 1234" }
```

### Требования в ТЗ

- Не хранить CVV.
- Пароли — только hash (bcrypt, argon2).
- PII — маскировать в логах.
- Не передавать в URL (только в body).

---

## 5. Защита от атак

| Атака | Защита |
|---|---|
| **SQL Injection** | Параметризованные запросы, ORM |
| **XSS** | Экранирование, CSP |
| **CSRF** | CSRF-токены, SameSite cookies |
| **SSRF** | Whitelist URL, запрет internal IP |
| **Mass Assignment** | Явный whitelist полей |
| **Timing attack** | Constant-time сравнение |
| **Replay** | Таймстамп + nonce |
| **Brute force** | Rate limiting, CAPTCHA |

### Mass Assignment

**Плохо:** клиент может передать `"role": "admin"`.

**Хорошо:**
```json
{ "name": "Иван", "email": "ivan@example.com" }
```
Только разрешённые поля. Сервер сам устанавливает роль.

### SSRF

**Плохо:** API принимает URL и делает запрос куда угодно.
**Хорошо:** whitelist доменов, запрет `localhost`, `169.254.0.0/16`, `10.0.0.0/8`.

---

## 6. Rate limiting

### Алгоритмы

| Алгоритм | Особенности |
|---|---|
| Fixed window | Просто, но резкие границы |
| Sliding window | Точнее |
| Token bucket | Плавно, burst разрешён |
| Leaky bucket | Ровный поток |

### Уровни

- По IP.
- По пользователю.
- По API-ключу.
- По endpoint.

### Заголовки

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 990
X-RateLimit-Reset: 1737003600
```

### При превышении

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

**В ТЗ:** указать лимиты для каждого endpoint'а.

---

## 7. Аудит и логирование

Что логировать:
- Кто (user_id, IP).
- Что (endpoint, метод).
- Когда (timestamp).
- Результат (код).
- Изменения (before / after для критичных).

**Что НЕ логировать:**
- Пароли.
- Токены.
- Полные номера карт.

**Retention:** типично 1–3 года для аудита.

---

## 8. Требования к API в ТЗ

Для каждого endpoint'а:

- [ ] Аутентификация (какой тип).
- [ ] Авторизация (какая роль, scope).
- [ ] Проверка владения объектом.
- [ ] Whitelist входных полей.
- [ ] Валидация типов и форматов.
- [ ] Лимиты (rate, размер body).
- [ ] Логирование (что, где).
- [ ] Маскирование PII.

---

## 9. Практика

### Задача 1
Опишите защиту для `GET /orders/{id}`.

| Требование | Значение |
|---|---|
| Аутентификация | Bearer JWT |
| Авторизация | Пользователь может читать свои заказы |
| Владение | `order.user_id == token.sub` или роль `admin` |
| Rate limit | 100/мин на пользователя |
| Логирование | `user_id`, `order_id`, `status` |
| Маскирование | `user.phone`, `user.email` |

### Задача 2
Опишите whitelist для создания заказа.

**Разрешённые поля:**
- `external_id` (string, 1–64 символа).
- `user_id` (int, > 0).
- `items` (array, 1–100 элементов).
  - `product_id` (int).
  - `quantity` (int, 1–1000).

**Запрещённые:** `status`, `total`, `created_at`, `role`, `id`.

### Задача 3
Опишите rate limiting.

| Endpoint | Лимит | Окно |
|---|---|---|
| POST /orders | 10 | минута |
| GET /orders | 100 | минута |
| POST /auth/login | 5 | минута |
| GET /products | 1000 | минута |

При превышении: `429` + `Retry-After`.

### Задача 4
Опишите аудит.

**Таблица `audit_log`:**

| Поле | Тип |
|---|---|
| id | bigint |
| user_id | bigint |
| action | varchar |
| entity_type | varchar |
| entity_id | bigint |
| before | jsonb |
| after | jsonb |
| ip | varchar |
| user_agent | varchar |
| created_at | timestamptz |

**Пример записи:** `user 123 обновил order 456, статус с created на paid`.

---

## 10. Чек-лист

- [ ] Знаю OWASP API Top 10
- [ ] Проверяю владение объектом (BOLA/IDOR)
- [ ] Описываю RBAC / ABAC
- [ ] Маскирую PII в логах
- [ ] Защищаюсь от SQL injection, XSS, CSRF, SSRF
- [ ] Описываю rate limiting
- [ ] Веду аудит критичных операций
- [ ] Формирую чек-лист безопасности для каждого endpoint'а
