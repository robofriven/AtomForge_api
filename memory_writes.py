# memory_writes.py
#
# Minimal “LLM writes -> AtomSpace links” glue.
# Schema expected from ChatGPT:
# {
#   "writes": [
#     ["IsA", "Greg", "Human"],
#     ["HasA", "Greg", "Coffee"]
#   ],
#   "assistant_text": "optional"
# }

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence, Tuple, Union


JSONLike = Union[dict, list, str, int, float, bool, None]


@dataclass(frozen=True)
class ApplyResult:
    link_ids: List[int]
    errors: List[str]
    assistant_text: Optional[str] = None


def _strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        # remove first fence line
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1 :]
        # remove trailing fence
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def parse_llm_json(text: str) -> dict:
    """
    Robust-ish JSON extractor for model outputs that may include code fences.
    Assumes the model outputs a single JSON object.
    """
    s = _strip_code_fences(text)

    # Try direct parse first.
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
        raise TypeError(f"Expected a JSON object, got {type(obj).__name__}")
    except json.JSONDecodeError:
        pass

    # Fallback: find first '{' ... last '}' and parse that slice.
    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Could not find a JSON object in the model output.")
    snippet = s[start : end + 1]
    obj = json.loads(snippet)
    if not isinstance(obj, dict):
        raise TypeError(f"Expected a JSON object, got {type(obj).__name__}")
    return obj


def _validate_write_entry(entry: Any) -> Tuple[Optional[str], List[str]]:
    """
    Returns (predicate, labels) if valid-ish, otherwise (None, []).
    """
    if not isinstance(entry, (list, tuple)):
        return None, []
    if len(entry) < 2:
        return None, []
    pred = entry[0]
    if not isinstance(pred, str) or not pred.strip():
        return None, []
    labels: List[str] = []
    for x in entry[1:]:
        if not isinstance(x, str) or not x.strip():
            return None, []
        labels.append(x.strip())
    return pred.strip(), labels


def apply_writes(space: Any, writes: Sequence[Sequence[str]]) -> ApplyResult:
    """
    Applies flat link writes into your AtomSpace.

    Each write entry shape:
      [predicate_name, arg1_label, arg2_label, ...]

    Implementation details:
      - Each label becomes an Entity node (interned).
      - Then we call space.add.link(predicate_name, *arg_ids)
        which uses your predicate registry / arity validation.

    Returns:
      ApplyResult(link_ids=[...], errors=[...])
    """
    link_ids: List[int] = []
    errors: List[str] = []

    for i, entry in enumerate(writes):
        pred, labels = _validate_write_entry(entry)
        if pred is None:
            errors.append(
                f"writes[{i}] invalid: expected [Pred, 'label', ...], got {entry!r}"
            )
            continue

        try:
            arg_ids = [space.add.entity(lbl) for lbl in labels]
        except Exception as e:
            errors.append(f"writes[{i}] failed creating nodes for {labels!r}: {e}")
            continue

        try:
            lid = space.add.link(pred, *arg_ids)
            link_ids.append(int(lid))
        except Exception as e:
            errors.append(f"writes[{i}] failed link {pred}({labels}): {e}")
            continue

    assistant_text = None
    # caller can set this if they pass parsed json with assistant_text
    return ApplyResult(link_ids=link_ids, errors=errors, assistant_text=assistant_text)


def apply_llm_output(space: Any, llm_text: str) -> ApplyResult:
    """
    One-stop: parse model output -> apply writes -> return result.
    """
    obj = parse_llm_json(llm_text)

    writes_raw = obj.get("writes", [])
    if not isinstance(writes_raw, list):
        return ApplyResult(
            link_ids=[],
            errors=["'writes' must be a list"],
            assistant_text=obj.get("assistant_text"),
        )

    result = apply_writes(space, writes_raw)
    return ApplyResult(
        link_ids=result.link_ids,
        errors=result.errors,
        assistant_text=obj.get("assistant_text"),
    )


# ---- Optional: tiny helper prompt you can stick in your system message ----

LLM_MEMORY_SCHEMA_INSTRUCTIONS = """\
When you learn stable facts, output a single JSON object with:
- "writes": a list of arrays shaped [PredicateName, "ArgLabel1", "ArgLabel2", ...]
Only use these PredicateName values: IsA, HasA, Wants, Believes, HappensAt, Not, Because, Claims, Called, Causes, At, During, Does, Sees, IsFeeling, With, Axiom.
Do not invent new predicate names.
Also include "assistant_text" with your normal reply.
Output ONLY the JSON.
"""
