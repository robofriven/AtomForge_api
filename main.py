# main.py
from build_app import create_app
from schemas import MemoryWriteRequest
from memory_logic import apply_memory_writes

app = create_app()


@app.post("/memory/write")
def memory_write(req: MemoryWriteRequest):
    mem = app.state.mem
    render = app.state.render
    return apply_memory_writes(mem, render, req.writes)
