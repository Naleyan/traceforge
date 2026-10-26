import json
import logging
import sys
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request


class JsonFormatter(logging.Formatter):
    """Transforme chaque log en une ligne JSON, avec les identifiants de trace injectés par ddtrace."""

    def format(self, record: logging.LogRecord) -> str:
        log = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            # Ajoutés par ddtrace si le log est écrit pendant une requête tracée
            "dd.trace_id": str(getattr(record, "dd.trace_id", "0")),
            "dd.span_id": str(getattr(record, "dd.span_id", "0")),
            "dd.service": getattr(record, "dd.service", ""),
            "dd.env": getattr(record, "dd.env", ""),
            "dd.version": getattr(record, "dd.version", ""),
        }
        # Champs supplémentaires passés avec extra={"fields": {...}}
        log.update(getattr(record, "fields", {}))
        if record.exc_info:
            log["error.stack"] = self.formatException(record.exc_info)
        return json.dumps(log, ensure_ascii=False)


def setup_logging(app: FastAPI) -> logging.Logger:
    """Configure les logs JSON et ajoute un log structuré pour chaque requête reçue."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)

    logger = logging.getLogger("app")

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # On ne logue pas les healthchecks, qui arrivent toutes les 5 secondes
        if request.url.path != "/health":
            status = response.status_code
            level = logging.ERROR if status >= 500 else logging.WARNING if status >= 400 else logging.INFO
            logger.log(
                level,
                f"{request.method} {request.url.path} {status}",
                extra={"fields": {
                    "http.method": request.method,
                    "http.url_details.path": request.url.path,
                    "http.status_code": status,
                    "duration_ms": duration_ms,
                }},
            )
        return response

    return logger