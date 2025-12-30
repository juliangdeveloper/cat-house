"""
Production-ready logging configuration with structured JSON logging for CloudWatch.
"""

import json
import sys
from contextvars import ContextVar

from loguru import logger

from app.config import settings

# Context variable for trace ID (correlation ID)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def serialize_log(record):
    """Serialize log record to JSON for CloudWatch."""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "service": settings.service_name,
        "trace_id": trace_id_var.get(),
        "message": record["message"],
        "function": record["function"],
        "line": record["line"],
        "extra": record["extra"],
    }
    return json.dumps(subset)


def patched_serialize(text):
    """Patch function to include trace_id in all logs."""
    record = json.loads(text)
    record["trace_id"] = trace_id_var.get()
    return json.dumps(record)


def setup_logging():
    """Configure logging based on environment."""
    logger.remove()  # Remove default handler

    if settings.environment == "development":
        # Development: Colored output to stdout
        logger.add(
            sys.stdout,
            level="DEBUG",
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )
    else:
        # Production/Staging: JSON output to stdout (CloudWatch)
        def json_sink(message):
            record = message.record
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "service": settings.service_name,
                "trace_id": trace_id_var.get(),
                "message": record["message"],
                "function": record["function"],
                "line": record["line"],
                "extra": record["extra"],
            }
            print(json.dumps(log_entry), flush=True)

        logger.add(json_sink, level="INFO")

    logger.info(f"Logging configured for environment: {settings.environment}")


# Export configured logger
__all__ = ["logger", "trace_id_var", "setup_logging"]
