"""
app/core/logging.py
────────────────────────────────────────────────────────────────────────────
Central logging configuration for the Library API.

Design choices
──────────────
• A single call to `configure_logging()` (made once at application startup)
  wires up the root logger so every module that does
  ``logger = logging.getLogger(__name__)`` automatically inherits the format.
• Format: ISO-8601 timestamp | level | logger name | message.
  In DEBUG mode an extra [request_id] field is emitted when the
  RequestLoggingMiddleware stores one on the context-var.
• In production (DEBUG=False) the level is INFO; locally it is DEBUG.
• SQLAlchemy engine chatter is kept at WARNING unless DEBUG is on.
"""
from __future__ import annotations

import logging
import logging.config
import sys
from contextvars import ContextVar

# Per-request correlation ID stored by RequestLoggingMiddleware
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    """Inject the current request-id into every LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get("-")
        return True


def configure_logging(debug: bool = False) -> None:
    """Call once at startup (before the first import that logs anything)."""

    level = "DEBUG" if debug else "INFO"
    sa_level = "DEBUG" if debug else "WARNING"

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": _RequestIdFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)-8s | %(name)s"
                    " | [%(request_id)s] %(message)s"
                ),
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "standard",
                "filters": ["request_id"],
            },
        },
        "loggers": {
            # Our application code
            "app": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
            # SQLAlchemy — noisy by default; only surface warnings in prod
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": sa_level,
                "propagate": False,
            },
            # Alembic migrations
            "alembic": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            # Uvicorn access log is already structured; we just tame the level
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }

    logging.config.dictConfig(config)
