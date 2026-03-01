from __future__ import annotations

import secrets
import sys
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

Sink = Callable[[str, str, str, str], None]
# Arguments: (timestamp, source, operation, formatted_message)


def _current_time_hms() -> str:
    # Local time, no date, no milliseconds (as decided)
    return time.strftime("%H:%M:%S", time.localtime())


def _generate_short_request_id(n_bytes: int = 2) -> str:
    # 2 bytes = 4 hex characters (e.g., "9f2a")
    return secrets.token_hex(n_bytes)


@dataclass
class Monitor:
    """
    Minimal structured runtime monitor.

    Console format:
        HH:MM:SS [API] QRY: HasA(Becky, *) rid=9f2a

    Only ERR operations are colored red (TTY only).
    """

    enabled: bool = True
    sinks: Optional[List[Sink]] = None

    def __post_init__(self) -> None:
        if self.sinks is None:
            self.sinks = [self._stdout_sink]

    def new_request_id(self) -> str:
        return _generate_short_request_id()

    def add_sink(self, sink: Sink) -> None:
        if self.sinks is None:
            self.sinks = []
        self.sinks.append(sink)

    def log(
        self,
        *,
        source: str,
        operation: str,
        message: str,
        request_id: str,
    ) -> None:
        """
        Emit a single structured event.
        """

        if not self.enabled:
            return

        timestamp = _current_time_hms()

        # Keep console tags fixed-width (3 chars)
        source_tag = (source.strip().upper() + "   ")[:3]
        operation_tag = (operation.strip().upper() + "   ")[:3]

        formatted_message = f"{message} rid={request_id}"

        for sink in self.sinks or []:
            try:
                sink(timestamp, source_tag, operation_tag, formatted_message)
            except Exception:
                # Monitor must never break the application
                pass

    # -------------------------
    # Default stdout sink
    # -------------------------

    def _stdout_sink(
        self,
        timestamp: str,
        source: str,
        operation: str,
        formatted_message: str,
    ) -> None:
        line = f"{timestamp} [{source}] {operation}: {formatted_message}"

        # Only color ERR red (TTY only)
        if operation == "ERR" and sys.stdout.isatty():
            line = f"\033[31m{line}\033[0m"

        print(line, file=sys.stdout, flush=True)
