# Reliable Webhook Delivery

Flask webhook service using Redis and a background worker.

## Features
- Webhook registration
- Event publishing
- Redis delivery queue
- Background worker
- HMAC-SHA256 signatures
- Retry with exponential backoff
- Delivery status tracking

## Run

```bash
docker compose up --build
```

API: http://localhost:5000

Register:
```bash
curl -X POST http://localhost:5000/webhooks -H "Content-Type: application/json" -d '{"url":"https://example.com/webhook","secret":"my-secret"}'
```

Publish:
```bash
curl -X POST http://localhost:5000/events -H "Content-Type: application/json" -d '{"event":"order.created","data":{"order_id":"123"}}'
```

List webhooks:
```bash
curl http://localhost:5000/webhooks
```

Delivery:
```bash
curl http://localhost:5000/deliveries/<delivery_id>
```

Failed deliveries retry up to 5 attempts with exponential backoff.

Day 317 / 365
