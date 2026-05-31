from src.ingestion.document import ConfidenceObject, TemporalDocument
from src.llm import client
from src.synthesis import prompts

_PROMPT_MAP = {
    "answer": prompts.answer_prompt,
    "warn_stale": prompts.warn_stale_prompt,
    "surface_conflict": prompts.surface_conflict_prompt,
    "surface_supersession": prompts.surface_supersession_prompt,
    "refuse": prompts.refuse_prompt,
}

_MODEL_MAP = {
    "answer": client.MODEL_LARGE,
    "warn_stale": client.MODEL_SMALL,
    "surface_conflict": client.MODEL_LARGE,
    "surface_supersession": client.MODEL_LARGE,
    "refuse": client.MODEL_SMALL,
}


def synthesize(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> dict:
    action = confidence.recommended_action
    prompt_fn = _PROMPT_MAP[action]
    model = _MODEL_MAP[action]

    prompt = prompt_fn(query, chunks, confidence)
    answer = client.complete(prompt, model=model)

    return {
        "answer": answer,
        "confidence": confidence,
        "prompt_used": prompt_fn.__name__,
    }
