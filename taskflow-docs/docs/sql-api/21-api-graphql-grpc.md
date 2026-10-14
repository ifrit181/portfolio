# GraphQL, gRPC, WebSocket

## Содержание

1. Зачем аналитику знать альтернативы REST
2. GraphQL
3. gRPC
4. WebSocket
5. Server-Sent Events
6. Сравнение
7. Что описывать в ТЗ
8. Практика
9. Чек-лист

---

## 1. Зачем аналитику знать альтернативы REST

REST — не единственный стиль. В разных проектах встречаются GraphQL, gRPC, WebSocket. Аналитик должен понимать их назначение и уметь описать контракт.

---

## 2. GraphQL

**GraphQL** — язык запросов, где клиент сам выбирает поля.

### Схема

```graphql
type Order {
  id: ID!
  status: OrderStatus!
  total: Float!
  user: User!
  items: [OrderItem!]!
}

enum OrderStatus {
  CREATED
  PAID
  SHIPPED
  CANCELLED
}

type Query {
  order(id: ID!): Order
  orders(status: OrderStatus, limit: Int = 20): [Order!]!
}

type Mutation {
  createOrder(input: CreateOrderInput!): Order!
}
```

### Запрос

```graphql
query {
  order(id: "456") {
    id
    status
    total
    user { name email }
    items { productId quantity }
  }
}
```

### Ответ

```json
{
  "data": {
    "order": {
      "id": "456",
      "status": "PAID",
      "total": 1990.00,
      "user": { "name": "Иван", "email": "ivan@example.com" },
      "items": [{ "productId": "1", "quantity": 2 }]
    }
  }
}
```

### Плюсы

- Один endpoint — `/graphql`.
- Клиент берёт только нужные поля.
- Строгая типизация.
- Introspection — самодокументируемый.

### Минусы

- Сложнее кэширование.
- Проблема N+1 (решается DataLoader).
- Сложнее rate limiting.
- Query complexity — риск DoS.

### Что описывает аналитик

- Типы и поля.
- Запросы и мутации.
- Обязательность (`!`).
- Enum'ы.
- Ошибки в `errors`.

---

## 3. gRPC

**gRPC** — RPC-фреймворк от Google на HTTP/2 + Protocol Buffers.

### Контракт (.proto)

```protobuf
syntax = "proto3";

service OrderService {
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc CreateOrder (CreateOrderRequest) returns (Order);
  rpc StreamOrders (StreamRequest) returns (stream Order);
}

message Order {
  string id = 1;
  string status = 2;
  double total = 3;
  string user_id = 4;
}

message GetOrderRequest {
  string id = 1;
}

message CreateOrderRequest {
  string user_id = 1;
  repeated OrderItem items = 2;
}
```

### Особенности

- Бинарный формат (быстрее JSON).
- HTTP/2 (мультиплексирование).
- Строгая типизация.
- Кодогенерация клиентов.
- 4 типа методов: unary, server stream, client stream, bidirectional.

### Где использовать

- Микросервисы (внутренние вызовы).
- Высокие требования к latency.
- Стриминг.

### Где НЕ использовать

- Публичные API для браузеров.
- Простые CRUD.

---

## 4. WebSocket

**WebSocket** — двусторонний канал поверх TCP.

### Handshake

```http
GET /ws HTTP/1.1
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

Сервер отвечает `101 Switching Protocols`.

### Особенности

- Постоянное соединение.
- Двусторонняя передача.
- Низкая latency.
- Нет request-response (нужно самим проектировать протокол).

### Где использовать

- Чаты.
- Уведомления real-time.
- Трейдинг.
- Игры.
- Коллаборативные редакторы.

### Что описывает аналитик

- Формат сообщений (JSON).
- Типы сообщений (`subscribe`, `event`, `ping`, `pong`).
- Протокол авторизации.
- Переподключение.
- Heartbeat.

**Пример:**
```json
{ "type": "subscribe", "channel": "orders.123" }
{ "type": "event", "channel": "orders.123", "data": { "status": "paid" } }
{ "type": "ping" }
{ "type": "pong" }
```

---

## 5. Server-Sent Events (SSE)

**SSE** — односторонний поток от сервера к клиенту по HTTP.

```
GET /events HTTP/1.1
Accept: text/event-stream

data: {"type": "order.paid", "order_id": 456}

data: {"type": "order.shipped", "order_id": 456}
```

**Плюсы:** просто, работает через HTTP.
**Минусы:** только server → client.

**Где использовать:** уведомления, стриминг логов, прогресс операций.

---

## 6. Сравнение

| | REST | GraphQL | gRPC | WebSocket |
|---|---|---|---|---|
| Транспорт | HTTP/1.1, HTTP/2 | HTTP | HTTP/2 | TCP |
| Формат | JSON | JSON | Protobuf | Любой |
| Клиент → сервер | ✅ | ✅ | ✅ | ✅ |
| Сервер → клиент | ❌ | ❌ | Streaming | ✅ |
| Типизация | OpenAPI | SDL | .proto | — |
| Браузер | ✅ | ✅ | Ограниченно | ✅ |
| Кэш | ✅ | Сложно | ❌ | ❌ |
| Когда | Публичные API | Гибкие клиенты | Микросервисы | Real-time |

---

## 7. Что описывать в ТЗ

### GraphQL
- Типы, поля, обязательность.
- Queries и mutations.
- Аргументы и их типы.
- Ошибки.
- Лимиты глубины и сложности.

### gRPC
- Сервисы и методы.
- Сообщения (.proto).
- Тип метода (unary / stream).
- Коды ошибок (`INVALID_ARGUMENT`, `NOT_FOUND`, `UNAVAILABLE`).

### WebSocket
- URL подключения.
- Авторизация.
- Формат сообщений.
- Типы событий.
- Heartbeat и reconnect.
- Обработка ошибок.

### SSE
- URL.
- Формат событий.
- Reconnect (`Last-Event-ID`).

---

## 8. Практика

### Задача 1
Опишите GraphQL-схему для заказов.

```graphql
type Query {
  order(id: ID!): Order
  orders(userId: ID, status: OrderStatus, limit: Int = 20): [Order!]!
}

type Mutation {
  createOrder(input: CreateOrderInput!): Order!
  cancelOrder(id: ID!): Order!
}

input CreateOrderInput {
  userId: ID!
  items: [OrderItemInput!]!
}

input OrderItemInput {
  productId: ID!
  quantity: Int!
}
```

### Задача 2
Опишите WebSocket-протокол для уведомлений.

**Подключение:**
```
wss://api.example.com/ws?token=<jwt>
```

**Сообщения:**

| Тип | Направление | Payload |
|---|---|---|
| `subscribe` | client → server | `{ "channel": "orders.123" }` |
| `unsubscribe` | client → server | `{ "channel": "orders.123" }` |
| `event` | server → client | `{ "channel": "...", "data": {...} }` |
| `ping` | client → server | `{}` |
| `pong` | server → client | `{}` |

**Reconnect:** exponential backoff, max 5 попыток.
**Heartbeat:** ping каждые 30 секунд.

### Задача 3
Опишите gRPC-сервис для заказов.

```protobuf
service OrderService {
  rpc GetOrder (GetOrderRequest) returns (Order);
  rpc CreateOrder (CreateOrderRequest) returns (Order);
  rpc ListOrders (ListOrdersRequest) returns (ListOrdersResponse);
}

message Order {
  string id = 1;
  string status = 2;
  double total = 3;
}
```

---

## 9. Чек-лист

- [ ] Понимаю, зачем GraphQL и когда его использовать
- [ ] Умею читать и писать GraphQL-схему
- [ ] Знаю gRPC: protobuf, HTTP/2, streaming
- [ ] Понимаю WebSocket: handshake, протокол
- [ ] Знаю SSE
- [ ] Могу сравнить и выбрать подходящий подход
- [ ] Умею описывать контракт для каждой технологии
