import re

import spacy

_ENTITY_TYPES = frozenset(
    {"PERSON", "ORG", "GPE", "PRODUCT", "LAW", "DATE", "DISEASE", "DRUG"}
)

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_trf")
        except OSError:
            _nlp = spacy.load("en_core_web_lg")
    return _nlp


def _normalize(span) -> str:
    lemmas = [t.lemma_.lower() for t in span if not t.is_space]
    joined = " ".join(lemmas)
    return re.sub(r"[^\w\s]", "", joined).strip()


def extract_entities(text: str) -> list[dict]:
    nlp = _get_nlp()
    doc = nlp(text)
    seen: set[str] = set()
    entities = []
    for ent in doc.ents:
        if ent.label_ not in _ENTITY_TYPES:
            continue
        normalized = _normalize(ent)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        entities.append(
            {
                "name": ent.text,
                "entity_type": ent.label_,
                "normalized_name": normalized,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
            }
        )
    return entities
