import os
from enum import Enum

from src.ingestion.document import TemporalDocument
from src.llm.client import chat

import logging

_logger = logging.getLogger(__name__)

_SMALL_MODEL = os.getenv(
    "NVIDIA_MODEL_SMALL", "nvidia/llama-3.1-nemotron-nano-8b-v1"
)
_LARGE_MODEL = os.getenv(
    "NVIDIA_MODEL_LARGE", "nvidia/llama-3.3-nemotron-super-49b-v1"
)

_SUPERSESSION_PROMPT = (
    "Does text B update, replace, or revise the claim in text A? Answer yes or no.\n\n"
    "Text A: {text_a}\n\n"
    "Text B: {text_b}"
)

_POLICY_EXPANSION_PROMPT = (
    "Text A is from {date_a}. Text B is from {date_b}.\n"
    "Does Text B expand, relax, or remove a threshold or restriction "
    "that Text A established?\n"
    "Reply with a single word: yes or no.\n\n"
    "Text A: {text_a}\n\n"
    "Text B: {text_b}"
)

_POLICY_EXPANSION_DELTA_DAYS = 365


class ConflictType(str, Enum):
    NONE = "none"
    FLAT = "flat"
    TEMPORAL_SUPERSESSION = "temporal_supersession"


def _llm_yes(prompt: str, model: str = _SMALL_MODEL, max_tokens: int = 5) -> bool:
    response = chat(
        messages=[{"role": "user", "content": prompt}],
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
    )
    words = response.strip().split()
    if not words:
        _logger.warning("_llm_yes: empty response from model=%s", model)
        return False
    first = words[0].lower().rstrip(".,!?:")
    if first not in ("yes", "no"):
        _logger.warning("_llm_yes: unexpected first word %r from model=%s — defaulting NONE", first, model)
        return False
    return first == "yes"


def resolve(
    chunk_a: TemporalDocument,
    chunk_b: TemporalDocument,
    nli_result: dict,
) -> ConflictType:
    label = nli_result["label"]
    date_delta = abs((chunk_b.published_date - chunk_a.published_date).days)
    older = chunk_a if chunk_a.published_date <= chunk_b.published_date else chunk_b
    newer = chunk_b if chunk_a.published_date <= chunk_b.published_date else chunk_a

    if label == "contradiction":
        if date_delta < 30:
            return ConflictType.FLAT
        prompt = _SUPERSESSION_PROMPT.format(text_a=older.text, text_b=newer.text)
        return ConflictType.TEMPORAL_SUPERSESSION if _llm_yes(prompt) else ConflictType.FLAT

    if label == "neutral" and date_delta > _POLICY_EXPANSION_DELTA_DAYS:
        prompt = _POLICY_EXPANSION_PROMPT.format(
            date_a=older.published_date.strftime("%B %Y"),
            date_b=newer.published_date.strftime("%B %Y"),
            text_a=older.text,
            text_b=newer.text,
        )
        return (
            ConflictType.TEMPORAL_SUPERSESSION
            if _llm_yes(prompt, model=_LARGE_MODEL, max_tokens=10)
            else ConflictType.NONE
        )

    return ConflictType.NONE
