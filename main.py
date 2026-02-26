# main.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from build_app import create_app
from schemas import MemoryWriteRequest, MemoryQueryRequest  # <-- add MemoryQueryRequest

from memory_logic import (
    apply_memory_writes,
    apply_memory_query,
)  # <-- add apply_memory_query

app = create_app()


@app.post("/memory/write")
def memory_write(req: MemoryWriteRequest):
    mem = app.state.mem
    render = app.state.render
    return apply_memory_writes(
        mem,
        render,
        req.writes,
        write_log=app.state.write_log,
        source=req.source,
        session_id=req.session_id,
    )


@app.post("/memory/query")
def memory_query(req: MemoryQueryRequest):
    mem = app.state.mem
    render = app.state.render
    return apply_memory_query(
        mem,
        render,
        predicate=req.predicate,
        labels=req.labels,
        limit=req.limit,
        latest_only=req.latest_only,
    )


### Boring stuff
@app.get("/privacy")
def privacy():
    return HTMLResponse(open("privacy.html").read())
