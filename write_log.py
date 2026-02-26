# write_log.py
from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Any, Deque, Dict, List, Optional


@dataclass(frozen=True)
class WriteEvent:
    seq: int
    created_at_utc: str
    link_id: int
    pretty: str
    source: Optional[str] = None
    session_id: Optional[str] = None


class WriteLog:
    def __init__(self, max_events: int = 500) -> None:
        self.max_events = int(max_events)
        self._events: Deque[WriteEvent] = deque(maxlen=self.max_events)
        self._seq: int = 0

    def append(
        self,
        *,
        created_at_utc: str,
        link_id: int,
        pretty: str,
        source: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> WriteEvent:
        self._seq += 1
        ev = WriteEvent(
            seq=self._seq,
            created_at_utc=str(created_at_utc or ""),
            link_id=int(link_id),
            pretty=str(pretty),
            source=source,
            session_id=session_id,
        )
        self._events.append(ev)
        return ev

    def tail(
        self, n: int = 50, *, session_id: Optional[str] = None
    ) -> List[WriteEvent]:
        n = max(0, int(n))
        if n == 0:
            return []
        items = list(self._events)
        if session_id is not None:
            items = [e for e in items if e.session_id == session_id]
        return items[-n:]

    @staticmethod
    def to_dicts(events: List[WriteEvent]) -> List[Dict[str, Any]]:
        return [
            {
                "seq": e.seq,
                "created_at_utc": e.created_at_utc,
                "link_id": e.link_id,
                "pretty": e.pretty,
                "source": e.source,
                "session_id": e.session_id,
            }
            for e in events
        ]
