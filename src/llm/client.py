import json
import os
import re

from openai import OpenAI

MODEL_LARGE = os.getenv("NVIDIA_MODEL_LARGE", "nvidia/llama-3.3-nemotron-super-49b-v1")
MODEL_SMALL = os.getenv("NVIDIA_MODEL_SMALL", "nvidia/llama-3.1-nemotron-nano-8b-instruct")

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.getenv("NVIDIA_API_KEY", ""),
            base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
        )
    return _client


def chat(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    response = _get_client().chat.completions.create(
        model=model or MODEL_LARGE,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def complete(prompt: str, model: str = None, max_tokens: int = 1024) -> str:
    return chat(
        messages=[{"role": "user", "content": prompt}],
        model=model or MODEL_LARGE,
        max_tokens=max_tokens,
    )


def chat_json(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 512,
) -> dict:
    raw = chat(messages, model=model, max_tokens=max_tokens, temperature=0.1)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)
