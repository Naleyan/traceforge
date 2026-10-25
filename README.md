# TraceForge

Observability and incident diagnosis on a small microservice application, using Datadog.

## Architecture

- **gateway** (port 8000): entry point, orchestrates the order flow
- **product** (port 8001): product catalog
- **order** (port 8002): order management
- **payment** (port 8003): simulated payments

## Run

Requirements: Docker Desktop.

```bash
docker compose up --build
```

Then open http://localhost:8000/docs and call `POST /orders` with:

```json
{"product_id": "p1", "quantity": 2}
```

## Known limitations

- Data is stored in memory and lost on restart.
- Stock is not decremented.
- A payment timeout marks the order as `payment_failed`, although the payment may have succeeded.