# memory_logic.py
from memory_writes import apply_writes


def apply_memory_writes(mem, render, writes):
    """
    Core memory write logic.
    No FastAPI imports. Pure function style.
    """
    result = apply_writes(mem, writes)

    pretty = [
        {"link_id": lid, "pretty": render.render_pretty(lid)} for lid in result.link_ids
    ]

    return {
        "applied_link_ids": result.link_ids,
        "errors": result.errors,
        "pretty": pretty,
    }
