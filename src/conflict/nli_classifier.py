from sentence_transformers import CrossEncoder

_LABELS = ["contradiction", "entailment", "neutral"]
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/nli-deberta-v3-base")
    return _model


def classify_pair(text_a: str, text_b: str) -> dict:
    return classify_pairs([(text_a, text_b)])[0]


def classify_pairs(pairs: list[tuple[str, str]]) -> list[dict]:
    if not pairs:
        return []
    model = _get_model()
    scores = model.predict(pairs, apply_softmax=True)
    results = []
    for row in scores:
        idx = int(row.argmax())
        results.append({"label": _LABELS[idx], "score": float(row[idx])})
    return results
