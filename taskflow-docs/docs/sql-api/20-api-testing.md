# Тестирование API

## Содержание

1. Зачем аналитику тестировать API
2. Уровни тестирования
3. Postman
4. Contract testing
5. Mock-серверы
6. Нагрузочное тестирование
7. Проверка edge cases
8. Что аналитик тестирует сам
9. Практика
10. Чек-лист

---

## 1. Зачем аналитику тестировать API

Аналитик — первый, кто видит API до релиза. Он проверяет:
- контракт соответствует спецификации;
- данные сохраняются корректно;
- ошибки возвращаются правильно;
- edge cases обработаны.

Это не заменяет QA, но ловит проблемы раньше.

---

## 2. Уровни тестирования

| Уровень | Кто | Что проверяет |
|---|---|---|
| Unit | Разработчик | Логика функции |
| Integration | Разработчик / QA | Взаимодействие модулей |
| Contract | QA / аналитик | Соответствие контракту |
| E2E | QA | Полный сценарий |
| Load | QA / DevOps | Производительность |
| Security | Security | Уязвимости |

Аналитик чаще всего участвует в **contract** и **E2E**.

---

## 3. Postman

**Postman** — инструмент для отправки HTTP-запросов и тестирования API.

### Коллекции

Группируйте запросы по функциональности:
```
Orders API
├── Create order
├── Get order
├── List orders
├── Update order
└── Delete order
```

### Environments

Разные окружения — разные переменные:
```
{{base_url}} = https://api.example.com/v1
{{token}} = <access_token>
```

### Pre-request script

```javascript
// получить токен перед запросом
pm.sendRequest({
    url: pm.environment.get('auth_url') + '/token',
    method: 'POST',
    body: { mode: 'formdata', formdata: [...] }
}, function (err, res) {
    pm.environment.set('token', res.json().access_token);
});
```

### Tests (assertions)

```javascript
pm.test("Status 201", () => pm.response.to.have.status(201));
pm.test("Has order id", () => {
    pm.expect(pm.response.json()).to.have.property('id');
});
pm.test("Response time < 500ms", () => {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

### Runner

Запуск всей коллекции сразу, с отчётом.

### Newman

CLI-версия Postman для CI/CD:
```bash
newman run collection.json -e env.json
```

---

## 4. Contract testing

**Цель:** убедиться, что клиент и сервер соблюдают контракт.

### Pact

Клиент пишет ожидания («pact»), сервер проверяет.

**Пример pact-файла:**
```json
{
  "consumer": { "name": "ShopService" },
  "provider": { "name": "OrdersService" },
  "interactions": [
    {
      "description": "create order",
      "request": {
        "method": "POST",
        "path": "/api/v1/orders",
        "body": { "user_id": 123 }
      },
      "response": {
        "status": 201,
        "body": { "id": 456, "status": "created" }
      }
    }
  ]
}
```

**Плюсы:** ловит breaking changes до релиза.
**Минусы:** сложнее в настройке.

### OpenAPI-валидация

Проверка, что реальные ответы соответствуют OpenAPI-спецификации.

Инструменты: Dredd, Schemathesis.

---

## 5. Mock-серверы

**Mock** — фейковый API, отвечающий по спецификации.

**Зачем:**
- фронт разрабатывается параллельно с бэком;
- тесты без реального API;
- демо.

**Инструменты:**
- Postman Mock Server;
- WireMock;
- Mockoon;
- Prism (по OpenAPI).

**Prism:**
```bash
prism mock openapi.yaml
# сервер отвечает по спецификации
```

---

## 6. Нагрузочное тестирование

**Цель:** проверить поведение под нагрузкой.

| Инструмент | Особенности |
|---|---|
| JMeter | Классика, GUI |
| k6 | Скрипты на JS |
| Gatling | Scala, отчёты |
| Locust | Python |

**Что проверяет аналитик:**
- SLA (p95 latency, throughput);
- поведение при 429;
- деградация при 500.

**Типичные метрики:**
- RPS (requests per second);
- p50, p95, p99 latency;
- error rate.

---

## 7. Проверка edge cases

Аналитик обязан проверить:

| Кейс | Что проверяет |
|---|---|
| Пустой body | 400 / 422 |
| Отсутствующее обязательное поле | 400 / 422 |
| Неверный тип поля | 400 / 422 |
| Огромный payload | 413 / 400 |
| Невалидный токен | 401 |
| Истёкший токен | 401 |
| Нет прав | 403 |
| Несуществующий ресурс | 404 |
| Дубль | 409 |
| Превышение лимита | 429 |
| Ошибка сервера | 500, retry |
| Таймаут | retry + DLQ |
| Частичный bulk-успех | 207 |

### Пример проверки идемпотентности

1. `POST /orders` с `Idempotency-Key: abc`.
2. Ответ `201`, `id: 456`.
3. Повтор с тем же ключом.
4. Ответ `200`, `id: 456` (не `457`).

### Пример проверки webhook

1. Регистрация webhook на тестовый URL.
2. Триггер события.
3. Проверка подписи.
4. Проверка retry при `500`.

---

## 8. Что аналитик тестирует сам

- Спецификацию OpenAPI (валидность).
- Сценарии: успех, ошибки, edge cases.
- Формат ошибок.
- Идемпотентность.
- Соответствие данных в БД и ответе (SQL-проверка).
- Вебхуки (если есть тестовый URL).

**Что НЕ делает аналитик:**
- нагрузочные тесты (это QA / DevOps);
- security-тесты (это security);
- unit-тесты (это разработчик).

---

## 9. Практика

### Задача 1
Написать Postman-тесты для создания заказа.

```javascript
pm.test("Status 201", () => pm.response.to.have.status(201));

const body = pm.response.json();
pm.test("Has id", () => pm.expect(body).to.have.property('id'));
pm.test("Status is created", () => pm.expect(body.status).to.eql('created'));
pm.test("Has external_id", () => pm.expect(body.external_id).to.eql('MAG-001'));

pm.test("Response time OK", () => {
    pm.expect(pm.response.responseTime).to.be.below(500);
});

pm.environment.set('order_id', body.id);
```

### Задача 2
Проверить идемпотентность.

1. Отправить `POST /orders` с ключом `abc-123`.
2. Сохранить `id` из ответа.
3. Отправить тот же запрос с тем же ключом.
4. Проверить: тот же `id`, код `200` (или `201`).
5. Отправить запрос с тем же ключом, но другим телом → `422` `IDEMPOTENCY_KEY_CONFLICT`.

### Задача 3
Проверить webhook.

**Тестовый сервер:** webhook.site.
1. Зарегистрировать URL.
2. Триггернуть событие.
3. Проверить payload, заголовки, подпись.
4. Вернуть `500` — убедиться, что придёт повтор.

### Задача 4
Проверить edge cases через SQL.

```sql
-- после создания заказа через API
SELECT id, external_id, user_id, status, total
FROM orders
WHERE external_id = 'MAG-001';
```

**Проверить:**
- все поля заполнены;
- нет дублей по `external_id`;
- связанные `order_items` созданы атомарно.

---

## 10. Чек-лист

- [ ] Понимаю уровни тестирования
- [ ] Умею писать Postman-коллекции с тестами
- [ ] Использую environments и переменные
- [ ] Знаю про contract testing
- [ ] Умею поднять mock-сервер по OpenAPI
- [ ] Понимаю нагрузочное тестирование
- [ ] Проверяю edge cases (400, 401, 403, 404, 409, 429, 500)
- [ ] Проверяю идемпотентность и webhooks
- [ ] Сверяю данные через SQL после вызова API
