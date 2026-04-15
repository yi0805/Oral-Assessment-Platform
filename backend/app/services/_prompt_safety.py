from __future__ import annotations

import json
import re
from typing import Any

MAX_UNTRUSTED_CHARS = 12000

_ROLE_INJECTION_RE = re.compile(r"(?i)(^|\n)\s*(system|assistant|user)\s*:")

_ENVELOPE_TAGS = (
    "</student_answer>",
    "</main_question>",
    "</assessor>",
    "</rubric>",
    "</transcript>",
)


def sanitize_untrusted(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("```", "").replace("<|im_start|>", "").replace("<|im_end|>", "")
    cleaned = _ROLE_INJECTION_RE.sub(r"\1", cleaned)
    for tag in _ENVELOPE_TAGS:
        cleaned = cleaned.replace(tag, "")

    return cleaned.strip()


def truncate_for_prompt(text: str, max_chars: int = MAX_UNTRUSTED_CHARS) -> str:
    if len(text) <= max_chars:
        return text

    half = max_chars // 2
    dropped = len(text) - max_chars

    return f"{text[:half]}\n[...truncated {dropped} chars...]\n{text[-half:]}"


def extract_json_object(raw: str) -> Any:
    return _extract_and_parse(raw, opener="{", closer="}")


def extract_json_array(raw: str) -> Any:
    return _extract_and_parse(raw, opener="[", closer="]")


def _extract_and_parse(raw: str, opener: str, closer: str) -> Any:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()

    pattern = rf"{re.escape(opener)}.*{re.escape(closer)}"
    match = re.search(pattern, cleaned, re.DOTALL)

    if match:
        cleaned = match.group(0)

    try:
        return json.loads(cleaned)
    
    except json.JSONDecodeError as exc:
        raise ValueError(f"Could not parse LLM JSON payload: {exc}") from exc
