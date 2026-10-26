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
## Tests

Each service has its own test suite. Example for the gateway:

```bash
pip install -r services/gateway/requirements-dev.txt
cd services/gateway
python -m pytest -v
```

Gateway tests use [respx](https://lundberg.github.io/respx/) to mock downstream services,
including timeouts, unreachable services and 5xx errors.

CI (GitHub Actions) runs all test suites and builds the Docker images on every push.

## Known limitations

- Data is stored in memory and lost on restart.
- Stock is not decremented.
- A payment timeout marks the order as `payment_failed`, although the payment may have succeeded.