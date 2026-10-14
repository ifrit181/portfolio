# <a id="http-глубокое-погружение">HTTP: глубокое погружение</a>

## <a id="содержание">Содержание</a>

1. Зачем аналитику HTTP
2. Структура HTTP-сообщения
3. Методы HTTP
4. Идемпотентность и безопасность методов
5. Статус-коды
6. Заголовки
7. Content Negotiation
8. Cookies и сессии
9. CORS
10. Кэширование
11. HTTP/1.1 vs HTTP/2 vs HTTP/3
12. Практика
13. Чек-лист

---

## <a id="1-зачем-аналитику-http">1. Зачем аналитику HTTP</a>

API живёт по правилам HTTP. Аналитик описывает в ТЗ:
- какой метод используется;
- какие заголовки обязательны;
- какие коды возвращаются;
- как работает кэш.

Без понимания HTTP спецификация API будет неполной.

---

## <a id="2-структура-http-сообщения">2. Структура HTTP-сообщения</a>

### <a id="запрос">Запрос</a>

```
POST /api/v1/orders HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOi...
Accept: application/json
Content-Length: 87

{
  "user_id": 123,
  "items": [{"product_id": 1, "quantity": 2}]
}
```

| Часть | Что содержит |
|---|---|
| Request line | Метод + путь + версия |
| Headers | Метаданные (auth, content-type, accept) |
| Body | Данные (только для POST/PUT/PATCH) |

### <a id="ответ">Ответ</a>

```
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/orders/456

{
  "id": 456,
  "status": "created"
}
```

---

## <a id="3-методы-http">3. Методы HTTP</a>

| Метод | Назначение | Body | Идемпотентный | Безопасный |
|---|---|---|---|---|
| `GET` | Получить | ❌ | ✅ | ✅ |
| `HEAD` | Как GET, но без body | ❌ | ✅ | ✅ |
| `OPTIONS` | Узнать возможности | ❌ | ✅ | ✅ |
| `POST` | Создать / выполнить | ✅ | ❌ | ❌ |
| `PUT` | Заменить целиком | ✅ | ✅ | ❌ |
| `PATCH` | Обновить частично | ✅ | ⚠️ | ❌ |
| `DELETE` | Удалить | ❌ | ✅ | ❌ |

**Идемпотентный** = повторный вызов даёт тот же результат.
**Безопасный** = не меняет состояние.

### PUT vs PATCH

```http
PUT /users/123
{ "name": "Иван", "email": "ivan@example.com" }
# Все поля заменяются. Пропущенные — обнулятся.

PATCH /users/123
{ "email": "new@example.com" }
# Только email меняется, остальное сохраняется.
```

**В ТЗ:** для частичного обновления всегда указывать `PATCH`, а не `PUT`.

---

## <a id="4-статус-коды">4. Статус-коды</a>

### <a id="2xx-успех">2xx — успех</a>

| Код | Когда |
|---|---|
| `200 OK` | Стандартный успех (GET, PUT, PATCH) |
| `201 Created` | Ресурс создан (POST) |
| `202 Accepted` | Принято в обработку (async) |
| `204 No Content` | Успех без тела (DELETE) |

### <a id="3xx-редирект">3xx — редирект</a>

| Код | Когда |
|---|---|
| `301 Moved Permanently` | Ресурс переехал навсегда |
| `302 Found` | Временный редирект |
| `304 Not Modified` | Кэш актуален |

### <a id="4xx-ошибка-клиента">4xx — ошибка клиента</a>

| Код | Когда |
|---|---|
| `400 Bad Request` | Невалидный запрос |
| `401 Unauthorized` | Нет аутентификации |
| `403 Forbidden` | Нет прав |
| `404 Not Found` | Ресурс не найден |
| `405 Method Not Allowed` | Метод не поддерживается |
| `409 Conflict` | Конфликт (дубль, версия) |
| `410 Gone` | Ресурс удалён безвозвратно |
| `422 Unprocessable Entity` | Валидация не пройдена |
| `429 Too Many Requests` | Лимит запросов |

### <a id="5xx-ошибка-сервера">5xx — ошибка сервера</a>

| Код | Когда |
|---|---|
| `500 Internal Server Error` | Общая ошибка |
| `502 Bad Gateway` | Upstream недоступен |
| `503 Service Unavailable` | Сервис недоступен |
| `504 Gateway Timeout` | Upstream не ответил |

**Правило аналитика:** для каждого endpoint'а в спецификации перечислить все возможные коды.

---

## <a id="5-заголовки">5. Заголовки</a>

### Request headers

| Заголовок | Назначение |
|---|---|
| `Authorization` | Токен / ключ |
| `Content-Type` | Формат тела запроса |
| `Accept` | Ожидаемый формат ответа |
| `User-Agent` | Клиент |
| `X-Request-Id` | ID для трассировки |
| `Idempotency-Key` | Ключ идемпотентности |
| `If-None-Match` | Условный GET |
| `Accept-Language` | Язык ответа |

### Response headers

| Заголовок | Назначение |
|---|---|
| `Content-Type` | Формат ответа |
| `Content-Length` | Размер |
| `Location` | Ссылка на созданный ресурс |
| `ETag` | Версия ресурса |
| `Cache-Control` | Правила кэша |
| `Retry-After` | Когда повторить (429, 503) |
| `X-RateLimit-Limit` | Лимит запросов |
| `X-RateLimit-Remaining` | Осталось запросов |

---

## 6. Content Negotiation

Клиент сообщает, что хочет, через `Accept`. Сервер отвечает в подходящем формате.

```http
Accept: application/json
Accept: application/xml
Accept: application/json, application/xml;q=0.8
```

Если сервер не может — `406 Not Acceptable`.

**В ТЗ:** указать, какие форматы поддерживает API.

---

## <a id="7-cookies-и-сессии">7. Cookies и сессии</a>

```
Set-Cookie: session_id=abc123; HttpOnly; Secure; SameSite=Lax
```

| Атрибут | Значение |
|---|---|
| `HttpOnly` | Недоступна из JS |
| `Secure` | Только по HTTPS |
| `SameSite` | Защита от CSRF |
| `Max-Age` | Срок жизни |

**Для API чаще используют токены**, а не cookies. Но для браузерных клиентов cookies удобнее.

---

## 8. CORS

**CORS (Cross-Origin Resource Sharing)** — механизм, разрешающий браузеру обращаться к чужому домену.

Preflight-запрос:
```http
OPTIONS /api/v1/orders
Origin: https://shop.example.com
Access-Control-Request-Method: POST
```

Ответ:
```http
Access-Control-Allow-Origin: https://shop.example.com
Access-Control-Allow-Methods: GET, POST, PATCH
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

**Что описывает аналитик:**
- какие источники разрешены;
- какие методы;
- какие заголовки;
- нужны ли credentials.

---

## <a id="9-кэширование">9. Кэширование</a>

### Cache-Control

```http
Cache-Control: no-store
Cache-Control: no-cache
Cache-Control: max-age=3600, public
Cache-Control: private, max-age=600
```

### ETag + If-None-Match

1. Клиент получает ресурс с `ETag: "abc123"`.
2. При следующем запросе отправляет `If-None-Match: "abc123"`.
3. Если ресурс не изменился — сервер вернёт `304 Not Modified`.

### Last-Modified + If-Modified-Since

Аналогично, но по времени.

**В ТЗ:** указать, кэшируется ли endpoint и на сколько.

---

## <a id="10-http-1-1-vs-http-2-vs-http-3">10. HTTP/1.1 vs HTTP/2 vs HTTP/3</a>

| Версия | Особенности |
|---|---|
| HTTP/1.1 | Много соединений, head-of-line blocking |
| HTTP/2 | Мультиплексирование, server push |
| HTTP/3 | На QUIC (UDP), быстрее в потерях |

**Для аналитика:** влияет на latency, но контракт API не меняется.

---

## <a id="11-практика">11. Практика</a>

### <a id="задача-1">Задача 1</a>
Опишите заголовки для создания заказа.

```http
POST /api/v1/orders HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer <token>
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
X-Request-Id: 8a7b3c1d-...
Accept: application/json
```

### <a id="задача-2">Задача 2</a>
Опишите поведение при ошибке валидации.

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "items[0].quantity", "issue": "must be >= 1" }
    ]
  }
}
```

### <a id="задача-3">Задача 3</a>
Опишите кэширование GET /products.

```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=300
ETag: "v1-abc"

# повторный запрос
GET /products
If-None-Match: "v1-abc"

HTTP/1.1 304 Not Modified
```

---

## <a id="12-чек-лист">12. Чек-лист</a>

- [ ] Знаю структуру HTTP-запроса и ответа
- [ ] Понимаю идемпотентность и безопасность методов
- [ ] Знаю все статус-коды 2xx / 3xx / 4xx / 5xx
- [ ] Оперирую заголовками (`Authorization`, `Content-Type`, `ETag`)
- [ ] Понимаю Content Negotiation
- [ ] Знаю CORS и preflight
- [ ] Умею описывать кэширование
- [ ] Различаю HTTP/1.1, HTTP/2, HTTP/3
