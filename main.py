# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from build_app import create_app
from schemas import MemoryWriteRequest, MemoryQueryRequest  # <-- add MemoryQueryRequest

from memory_logic import (
    apply_memory_writes,
    apply_memory_query,
)


def _call(predicate: str, labels: list[str]) -> str:
    return f"{predicate}({', '.join(labels)})"


app = create_app()


@app.post("/memory/write")
def memory_write(req: MemoryWriteRequest):
    monitor = getattr(app.state, "monitor", None)
    request_id = monitor.new_request_id() if monitor is not None else "0000"

    if monitor is not None:
        for entry in req.writes:
            try:
                predicate = str(entry[0])
                labels = [str(x) for x in entry[1:]]
                monitor.log(
                    source="API",
                    operation="WRT",
                    message=_call(predicate, labels),
                    request_id=request_id,
                )
            except Exception:
                monitor.log(
                    source="API",
                    operation="ERR",
                    message=f"bad write entry: {entry!r}",
                    request_id=request_id,
                )

    mem = app.state.mem
    render = app.state.render
    return apply_memory_writes(
        mem,
        render,
        req.writes,
        write_log=app.state.write_log,
        monitor=monitor,
        request_id=request_id,
        source=req.source,
        session_id=req.session_id,
    )


@app.post("/memory/query")
def memory_query(req: MemoryQueryRequest):
    monitor = getattr(app.state, "monitor", None)
    request_id = monitor.new_request_id() if monitor is not None else "0000"

    # Normalize inputs (be tolerant)
    predicate = str(req.predicate).strip()

    try:
        labels = list(req.labels)
    except Exception:
        labels = [req.labels]
    labels = [str(x) for x in labels]

    # Validate
    if not predicate:
        if monitor is not None:
            monitor.log(
                source="API",
                operation="ERR",
                message="invalid query: empty predicate",
                request_id=request_id,
            )
        return {"links": [], "errors": ["predicate must be a non-empty string"]}

    if not labels:
        if monitor is not None:
            monitor.log(
                source="API",
                operation="ERR",
                message="invalid query: labels must not be empty",
                request_id=request_id,
            )
        return {"links": [], "errors": ["labels must not be empty"]}

    # Log intent
    if monitor is not None:
        monitor.log(
            source="API",
            operation="QRY",
            message=_call(predicate, labels),
            request_id=request_id,
        )

    mem = app.state.mem
    render = app.state.render
    return apply_memory_query(
        mem,
        render,
        predicate=predicate,
        labels=labels,
        limit=req.limit,
        latest_only=req.latest_only,
        monitor=monitor,
        request_id=request_id,
    )


### Boring stuff
@app.get("/privacy")
def privacy():
    return HTMLResponse(open("privacy.html").read())
