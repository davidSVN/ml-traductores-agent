import json
import logging
import os
import sys
from typing import Any, Optional, Union

_LOGGING_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str = "", env: str = "") -> None:
        super().__init__()
        self._service = service or os.getenv("SERVICE", "ml-traductores")
        self._env = env or os.getenv("ENV", "dev")

    def format(self, record: logging.LogRecord) -> str:
        from .context import get_context

        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self._service,
            "env": self._env,
        }

        ctx = get_context()
        for key, val in ctx.items():
            if val is not None:
                log_obj[key] = val

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        standard_attrs = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "exc_info", "exc_text", "thread", "threadName",
            "message", "asctime",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and value is not None:
                try:
                    json.dumps(value)
                    log_obj[key] = value
                except (TypeError, ValueError):
                    log_obj[key] = str(value)

        return json.dumps(log_obj, default=str)


def setup_logging(
    *,
    level: Optional[Union[int, str]] = None,
    service: str = "ml-traductores",
    env: str = "",
) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(level or os.getenv("LOG_LEVEL", "INFO"))

    for h in root.handlers[:]:
        root.removeHandler(h)

    formatter = JsonFormatter(service=service, env=env)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    from .context import LoggingContextFilter
    root.addFilter(LoggingContextFilter())

    _LOGGING_CONFIGURED = True
