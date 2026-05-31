from src.ingestion.document import ConfidenceObject, TemporalDocument

_GROUNDING = (
    "STRICT GROUNDING RULES — you must follow all of these:\n"
    "- Answer ONLY using the exact text provided in the context chunks below.\n"
    "- Do not add any information, links, or details not present in the chunks.\n"
    "- Do not invent URLs, citations, or references.\n"
    "- Do not include any URLs or web links in your response.\n"
    "- If the chunks do not contain enough information to answer fully, say so explicitly.\n\n"
)


def _format_sources(chunks: list[TemporalDocument]) -> str:
    parts = []
    for chunk in chunks:
        date_str = chunk.published_date.strftime("%Y-%m-%d")
        parts.append(f"[{chunk.source_id} | {date_str}]\n{chunk.text}")
    return "\n\n".join(parts)


def answer_prompt(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> str:
    return (
        f"{_GROUNDING}"
        "Answer the question using only the provided sources. "
        "Cite each source by its ID and publication date.\n\n"
        f"Question: {query}\n\n"
        f"Sources:\n{_format_sources(chunks)}\n\n"
        "Provide a direct, well-cited answer."
    )


def warn_stale_prompt(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> str:
    newest = confidence.newest_source_date.strftime("%Y-%m-%d")
    return (
        f"{_GROUNDING}"
        f"Answer the question using the provided sources. "
        f"The most recent source is from {newest}, which may be outdated. "
        "Include a clear staleness warning in your response.\n\n"
        f"Question: {query}\n\n"
        f"Sources:\n{_format_sources(chunks)}\n\n"
        f"Answer using only the chunk text above, and note that information reflects "
        f"knowledge as of {newest}."
    )


def surface_conflict_prompt(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> str:
    return (
        f"{_GROUNDING}"
        "The provided sources contain contradictory information. "
        "Present both positions clearly without resolving the conflict or synthesising a single answer. "
        "Cite source IDs and dates for each claim.\n\n"
        f"Question: {query}\n\n"
        f"Sources:\n{_format_sources(chunks)}\n\n"
        "Present the conflicting claims, one position per source."
    )


def surface_supersession_prompt(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> str:
    older_date = confidence.oldest_source_date.strftime("%Y-%m-%d")
    newer_date = confidence.newest_source_date.strftime("%Y-%m-%d")
    older_chunk = min(chunks, key=lambda c: c.published_date)
    newer_chunk = max(chunks, key=lambda c: c.published_date)
    return (
        f"{_GROUNDING}"
        "A newer source supersedes an older one on this topic. "
        "Use this format: \"As of [newer_date], [newer_source] states X. "
        "This supersedes [older_source] from [older_date] which stated Y.\"\n\n"
        f"Question: {query}\n\n"
        f"Older source [{older_chunk.source_id} | {older_date}]:\n{older_chunk.text}\n\n"
        f"Newer source [{newer_chunk.source_id} | {newer_date}]:\n{newer_chunk.text}\n\n"
        "Explain how guidance changed between the two sources."
    )


def refuse_prompt(
    query: str,
    chunks: list[TemporalDocument],
    confidence: ConfidenceObject,
) -> str:
    newest = confidence.newest_source_date.strftime("%Y-%m-%d")
    return (
        f"{_GROUNDING}"
        f"You cannot provide a reliable answer. "
        f"The available sources are too outdated (freshness: {confidence.freshness_score:.0%}) "
        f"or sources conflict too strongly (agreement: {confidence.source_agreement:.0%}). "
        "Explain this limitation and suggest what kind of fresher sources would help.\n\n"
        f"Question: {query}\n\n"
        f"Sources:\n{_format_sources(chunks)}\n\n"
        f"Newest available source date: {newest}\n\n"
        "Decline to answer and recommend what updated sources would be needed."
    )
