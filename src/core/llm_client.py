import json
import os
import re

from openai import OpenAI

_api_key = os.getenv("NVIDIA_API_KEY", "")
_base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
_default_model = os.getenv("NVIDIA_SYNTHESIS_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")

_client = OpenAI(api_key=_api_key, base_url=_base_url)


def chat(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> str:
    response = _client.chat.completions.create(
        model=model or _default_model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


def chat_json(
    messages: list[dict],
    model: str = None,
    max_tokens: int = 512,
) -> dict:
    raw = chat(messages, model=model, max_tokens=max_tokens, temperature=0.1)
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())
    return json.loads(cleaned)
