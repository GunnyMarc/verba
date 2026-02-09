"""Summarize video transcription using Ollama, OpenAI, Google Gemini, Anthropic, or Circuit."""

import os
import requests

from .config_manager import is_anthropic_model, is_circuit_model, is_google_model, is_openai_model


# Circuit model-name mapping to the actual model identifier on the Circuit API
CIRCUIT_MODEL_MAP = {
    "circuit-internal": "circuit-internal",
    "circuit-anthropic": "circuit-anthropic",
    "circuit-openai": "circuit-openai",
    "circuit-google": "circuit-google",
}

# Circuit API endpoint (OpenAI-compatible)
CIRCUIT_BASE_URL = os.environ.get("CIRCUIT_BASE_URL", "https://circuit.cisco.com/v1")


def summarize(transcript_text: str, instructions: str, model: str, base_url: str = "http://localhost:11434") -> str:
    """Send transcript for summarization using the provided instructions.

    Args:
        transcript_text: The markdown transcript content to summarize.
        instructions: Markdown instructions defining the desired summary format.
        model: Model name to use (Ollama, OpenAI, Google, or Circuit).
        base_url: Ollama API base URL (ignored for cloud models).

    Returns:
        The generated summary as a string.
    """
    if is_circuit_model(model):
        return _summarize_circuit(transcript_text, instructions, model)
    if is_anthropic_model(model):
        return _summarize_anthropic(transcript_text, instructions, model)
    if is_openai_model(model):
        return _summarize_openai(transcript_text, instructions, model)
    if is_google_model(model):
        return _summarize_google(transcript_text, instructions, model)
    return _summarize_ollama(transcript_text, instructions, model, base_url)


def _summarize_ollama(transcript_text: str, instructions: str, model: str, base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": transcript_text},
            ],
            "stream": False,
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _summarize_openai(transcript_text: str, instructions: str, model: str) -> str:
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY from env
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": transcript_text},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _summarize_anthropic(transcript_text: str, instructions: str, model: str) -> str:
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=model,
        system=instructions,
        messages=[
            {"role": "user", "content": transcript_text},
        ],
        max_tokens=4096,
    )
    return response.content[0].text


def _summarize_google(transcript_text: str, instructions: str, model: str) -> str:
    import google.generativeai as genai

    genai.configure()  # reads GOOGLE_API_KEY from env
    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=instructions,
    )
    response = gen_model.generate_content(transcript_text)
    return response.text


def _summarize_circuit(transcript_text: str, instructions: str, model: str) -> str:
    api_key = os.environ.get("CIRCUIT_API_KEY", "")
    if not api_key:
        raise RuntimeError("Circuit API key is not configured. Please add it in Settings.")

    circuit_model = CIRCUIT_MODEL_MAP.get(model, model)

    response = requests.post(
        f"{CIRCUIT_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": circuit_model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": transcript_text},
            ],
            "max_tokens": 4096,
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
