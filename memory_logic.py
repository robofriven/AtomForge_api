# memory_logic.py
from memory_writes import apply_writes
from typing import Any, Dict, List, Optional


def apply_memory_writes(
    mem,
    render,
    writes,
    *,
    write_log: Optional[Any] = None,
    source: Optional[str] = None,
    session_id: Optional[str] = None,
    context_n: int = 50,
):
    """
    Core memory write logic.
    No FastAPI imports. Pure function style.
    """
    result = apply_writes(mem, writes)

    pretty = [
        {"link_id": lid, "pretty": render.render_pretty(lid)} for lid in result.link_ids
    ]

    if write_log is not None:
        for row in pretty:
            lid = row["link_id"]
            created = getattr(mem.atom(lid), "crated_at_utc", "")
            write_log.append(
                created_at_utc=created,
                link_id=lid,
                pretty=row.get("pretty") or "",
                source=source,
                session_id=session_id,
            )
    context_log = []
    if write_log is not None:
        context_log = write_log.to_dicts(
            write_log.tail(context_n, session_id=session_id)
        )

    return {
        "applied_link_ids": result.link_ids,
        "errors": result.errors,
        "pretty": pretty,
        "context_log": context_log,
    }


def apply_memory_query(
    mem: Any,
    render: Any,
    *,
    predicate: str,
    labels: List[str],
    limit: int = 50,
    latest_only: bool = False,
) -> Dict[str, Any]:
    """
    Core memory query logic.
    Supports '*' wildcard in labels (handled by mem.retrieve.link_by_label).
    Returns link ids + args + pretty strings.
    """
    errors: List[str] = []
    links_out: List[Dict[str, Any]] = []

    if not isinstance(predicate, str) or not predicate.strip():
        return {"links": [], "errors": ["predicate must be a non-empty string"]}

    if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
        return {"links": [], "errors": ["labels must be a list of strings"]}

    try:
        results = mem.retrieve.link_by_label(predicate.strip(), *labels)
        # results: List[Tuple[lid, Tuple[arg_ids...]]]
    except Exception as e:
        return {"links": [], "errors": [str(e)]}

    # Optionally keep only the newest link (by created_at_utc)
    if latest_only and results:
        try:
            # created_at_utc is ISO-8601 (string); lexicographic sort works
            results = sorted(
                results,
                key=lambda pair: getattr(mem.atom(pair[0]), "created_at_utc", ""),
                reverse=True,
            )[:1]
        except Exception as e:
            errors.append(f"latest_only failed: {e}")

    # Apply limit (defensive)
    try:
        limit_n = int(limit)
    except Exception:
        limit_n = 50
    if limit_n < 1:
        limit_n = 1
    if limit_n > 1000:
        limit_n = 1000

    results = results[:limit_n]

    for lid, arg_ids in results:
        try:
            arg_labels = []
            for aid in arg_ids:
                a = mem.atom(aid)
                arg_labels.append(getattr(a, "label", None))
            pretty = render.render_pretty(lid)
        except Exception as e:
            errors.append(f"render failed for link {lid}: {e}")
            continue

        links_out.append(
            {
                "link_id": int(lid),
                "args": [int(x) for x in arg_ids],
                "arg_labels": arg_labels,
                "pretty": pretty,
            }
        )

    return {"links": links_out, "errors": errors}
