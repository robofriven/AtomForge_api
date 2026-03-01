# memory_logic.py
from memory_writes import apply_writes
from typing import Any, Dict, List, Optional


def apply_memory_writes(
    mem,
    render,
    writes,
    *,
    write_log=None,
    monitor=None,
    request_id=None,
    source=None,
    session_id=None,
    context_n=50,
):
    result = apply_writes(mem, writes)

    pretty = [
        {"link_id": lid, "pretty": render.render_pretty(lid)} for lid in result.link_ids
    ]

    # ---- Monitor output ----
    if monitor is not None and request_id:
        monitor.log(
            source="MEM",
            operation="RES",
            message=f"ok={len(result.link_ids)} err={len(result.errors)}",
            request_id=request_id,
        )

        for row in pretty:
            p = row.get("pretty") or ""
            if p:
                monitor.log(
                    source="MEM",
                    operation="WRT",
                    message=p,
                    request_id=request_id,
                )

        for e in result.errors:
            monitor.log(
                source="MEM",
                operation="ERR",
                message=str(e),
                request_id=request_id,
            )

    # ---- Write log ----
    if write_log is not None:
        for row in pretty:
            lid = row["link_id"]
            created = getattr(mem.atom(lid), "created_at_utc", "")
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
    mem,
    render,
    *,
    predicate: str,
    labels: list[str],
    limit: int = 50,
    latest_only: bool = False,
    monitor=None,
    request_id=None,
):
    errors: List[str] = []
    links_out: List[Dict[str, Any]] = []

    # ---- Normalize inputs ----
    predicate = str(predicate).strip()

    try:
        labels = list(labels)
    except Exception:
        labels = [labels]

    labels = [str(x) for x in labels]

    if not predicate:
        return {"links": [], "errors": ["predicate must be a non-empty string"]}

    if not labels:
        return {"links": [], "errors": ["labels must not be empty"]}

    # ---- Retrieve ----
    try:
        results = mem.retrieve.link_by_label(predicate, *labels)
        total_hits = len(results)
    except Exception as e:
        if monitor is not None and request_id:
            monitor.log(
                source="MEM", operation="ERR", message=str(e), request_id=request_id
            )
            monitor.log(
                source="MEM",
                operation="RES",
                message="hits=0 shown=0 err=1",
                request_id=request_id,
            )
        return {"links": [], "errors": [str(e)]}

    # ---- latest_only ----
    if latest_only and results:
        try:
            results = sorted(
                results,
                key=lambda pair: getattr(mem.atom(pair[0]), "created_at_utc", ""),
                reverse=True,
            )[:1]
        except Exception as e:
            errors.append(f"latest_only failed: {e}")

    # ---- Limit ----
    try:
        limit_n = int(limit)
    except Exception:
        limit_n = 50

    limit_n = max(1, min(limit_n, 1000))
    results = results[:limit_n]

    shown = len(results)

    # ---- Build output ----
    for lid, arg_ids in results:
        try:
            arg_labels = []
            for aid in arg_ids:
                a = mem.atom(aid)
                arg_labels.append(getattr(a, "label", None))
            pretty = render.render_pretty(lid)
        except Exception as e:
            msg = f"render failed for link {lid}: {e}"
            errors.append(msg)
            if monitor is not None and request_id:
                monitor.log(
                    source="MEM", operation="ERR", message=msg, request_id=request_id
                )
            continue

        links_out.append(
            {
                "link_id": int(lid),
                "args": [int(x) for x in arg_ids],
                "arg_labels": arg_labels,
                "pretty": pretty,
            }
        )

    # ---- Monitor output ----
    if monitor is not None and request_id:
        monitor.log(
            source="MEM",
            operation="RES",
            message=f"hits={total_hits} shown={shown} err={len(errors)}",
            request_id=request_id,
        )

        for row in links_out:
            p = row.get("pretty") or ""
            if p:
                monitor.log(
                    source="MEM",
                    operation="HIT",
                    message=p,
                    request_id=request_id,
                )

        for e in errors:
            monitor.log(
                source="MEM",
                operation="ERR",
                message=str(e),
                request_id=request_id,
            )

    return {"links": links_out, "errors": errors}

