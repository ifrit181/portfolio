# <a id="api-документирование-через-openapi-swagger">API: Документирование через OpenAPI / Swagger</a>

## <a id="содержание">Содержание</a>
1. Что такое OpenAPI
2. Структура спецификации
3. Описание endpoint'а
4. Схемы данных (components)
5. Параметры
6. Ответы и ошибки
7. Инструменты
8. Практика

---

## <a id="1-что-такое-openapi">1. Что такое OpenAPI</a>

**OpenAPI (бывший Swagger)** — стандарт описания REST API в формате YAML или JSON.

**Что даёт:**
- единый контракт между командами;
- автогенерация документации (Swagger UI);
- генерация клиентов и моков;
- валидация запросов.

---

## <a id="2-структура-спецификации">2. Структура спецификации</a>

```yaml
openapi: 3.0.3
info:
  title: Orders API
  version: 1.0.0
  description: API для управления заказами

servers:
  - url: https://api.example.com/v1

paths:
  /orders:
    get: ...
    post: ...

components:
  schemas:
    Order: ...
  securitySchemes:
    bearerAuth: ...
```

---

## <a id="3-описание-endpoint-а">3. Описание endpoint'а</a>

```yaml
paths:
  /orders/{id}:
    get:
      summary: Получить заказ по ID
      operationId: getOrderById
      tags:
        - Orders
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
            example: 456
      responses:
        '200':
          description: Успех
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '404':
          description: Заказ не найден
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
```

---

## <a id="4-схемы-данных-components">4. Схемы данных (components)</a>

```yaml
components:
  schemas:
    Order:
      type: object
      required:
        - id
        - user_id
        - status
        - total
      properties:
        id:
          type: integer
          example: 456
        user_id:
          type: integer
          example: 123
        status:
          type: string
          enum: [created, paid, shipped, cancelled]
        total:
          type: number
          format: decimal
          example: 1990.00
        created_at:
          type: string
          format: date-time
          example: '2026-01-15T10:30:00Z'
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'

    OrderItem:
      type: object
      properties:
        product_id:
          type: integer
        quantity:
          type: integer
          minimum: 1

    Error:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
```

---

## <a id="5-параметры">5. Параметры</a>

### Path

```yaml
parameters:
  - name: id
    in: path
    required: true
    schema:
      type: integer
```

### Query

```yaml
parameters:
  - name: status
    in: query
    schema:
      type: string
      enum: [created, paid, shipped]
  - name: page
    in: query
    schema:
      type: integer
      default: 1
      minimum: 1
  - name: limit
    in: query
    schema:
      type: integer
      default: 20
      maximum: 100
```

### Header

```yaml
parameters:
  - name: X-Request-Id
    in: header
    schema:
      type: string
      format: uuid
```

---

## <a id="6-ответы-и-ошибки">6. Ответы и ошибки</a>

```yaml
responses:
  '200':
    description: Список заказов
    content:
      application/json:
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                $ref: '#/components/schemas/Order'
            pagination:
              $ref: '#/components/schemas/Pagination'
  '400':
    $ref: '#/components/responses/BadRequest'
  '401':
    $ref: '#/components/responses/Unauthorized'
  '500':
    $ref: '#/components/responses/InternalError'

components:
  responses:
    BadRequest:
      description: Невалидные данные
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
```

---

## <a id="7-инструменты">7. Инструменты</a>

| Инструмент | Назначение |
|---|---|
| Swagger Editor | Онлайн-редактор OpenAPI |
| Swagger UI | Автогенерация документации |
| Postman | Тестирование по спецификации |
| Stoplight | Проектирование API |
| Redoc | Красивая документация |

**Workflow аналитика:**
1. Пишет спецификацию в Swagger Editor.
2. Проверяет в Swagger UI.
3. Отдаёт разработчикам.
4. Тестирует через Postman.

---

## <a id="8-практика">8. Практика</a>

### <a id="задача-1">Задача 1</a>
Опишите endpoint создания заказа.

```yaml
paths:
  /orders:
    post:
      summary: Создать заказ
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [user_id, items]
              properties:
                user_id:
                  type: integer
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/OrderItem'
      responses:
        '201':
          description: Создано
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
        '400':
          description: Ошибка валидации
        '401':
          description: Не авторизован
```

### <a id="задача-2">Задача 2</a>
Опишите схему пагинации.

```yaml
Pagination:
  type: object
  properties:
    page:
      type: integer
    limit:
      type: integer
    total:
      type: integer
    total_pages:
      type: integer
```

---

## <a id="чек-лист">Чек-лист</a>

- [ ] Понимаю структуру OpenAPI
- [ ] Описываю endpoint'ы, параметры, ответы
- [ ] Работаю с `components/schemas`
- [ ] Описываю ошибки через `$ref`
- [ ] Проверяю спецификацию в Swagger UI
- [ ] Тестирую через Postman
