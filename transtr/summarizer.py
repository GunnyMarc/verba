"""Summarize video transcription using Ollama, OpenAI, or Google Gemini."""

import requests

from .config_manager import is_google_model, is_openai_model


def summarize(transcript_text: str, instructions: str, model: str, base_url: str = "http://localhost:11434") -> str:
    """Send transcript for summarization using the provided instructions.

    Args:
        transcript_text: The markdown transcript content to summarize.
        instructions: Markdown instructions defining the desired summary format.
        model: Model name to use (Ollama, OpenAI, or Google).
        base_url: Ollama API base URL (ignored for cloud models).

    Returns:
        The generated summary as a string.
    """
    if is_openai_model(model):
        return _summarize_openai(transcript_text, instructions, model)
    if is_google_model(model):
        return _summarize_google(transcript_text, instructions, model)
    return _summarize_ollama(transcript_text, instructions, model, base_url)


def _summarize_ollama(transcript_text: str, instructions: str, model: str, base_url: str) -> str:
    response = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "system": instructions,
            "prompt": transcript_text,
            "stream": False,
        },
        timeout=600,
    )
    response.raise_for_status()
    return response.json()["response"]


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


def _summarize_google(transcript_text: str, instructions: str, model: str) -> str:
    import google.generativeai as genai

    genai.configure()  # reads GOOGLE_API_KEY from env
    gen_model = genai.GenerativeModel(
        model_name=model,
        system_instruction=instructions,
    )
    response = gen_model.generate_content(transcript_text)
    return response.text
