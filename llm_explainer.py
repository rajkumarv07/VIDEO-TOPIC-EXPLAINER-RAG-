"""
llm_explainer.py
Generates beginner-friendly explanations for topics using Groq LLM API.
"""

import os
import logging
from typing import List, Dict
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Supported models (fast & capable on Groq)
SUPPORTED_MODELS = {
    "llama-3.1-8b-instant": "Llama 3.1 8B (Fast)",
    "llama-3.3-70b-versatile": "Llama 3.3 70B (Powerful)",
    "mixtral-saba-24b": "Mixtral Saba 24B (Balanced)",
}

DEFAULT_MODEL = "llama-3.1-8b-instant"


def get_groq_client() -> Groq:
    """Create and return a Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. Please set it in your .env file."
        )
    return Groq(api_key=api_key)


def build_explanation_prompt(topics: List[str]) -> str:
    """Build a structured prompt for beginner-friendly explanations."""
    topics_str = ", ".join(topics)
    return f"""You are a friendly and clear educator. Your job is to explain technical and conceptual topics to complete beginners.

For each of the following topics, provide:
1. A simple 1-sentence definition.
2. A real-world analogy or example (1–2 sentences).
3. Why it matters or where it's used (1 sentence).

Topics to explain: {topics_str}

Format your response clearly with each topic as a heading followed by the explanation. Use plain language — avoid jargon. Be concise but informative."""


def explain_topics(
    topics: List[str],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.5
) -> Dict[str, str]:
    """
    Send topics to the Groq LLM API and get beginner-friendly explanations.

    Args:
        topics: List of topic strings to explain.
        model: Groq model ID to use.
        temperature: Sampling temperature (lower = more deterministic).

    Returns:
        Dictionary with keys:
          - 'raw_response': Full LLM response text.
          - 'model_used': Model ID that generated the response.

    Raises:
        EnvironmentError: If GROQ_API_KEY is missing.
        RuntimeError: If the API call fails.
    """
    if not topics:
        raise ValueError("No topics provided for explanation.")

    if model not in SUPPORTED_MODELS:
        logger.warning(f"Model '{model}' not in supported list. Using default.")
        model = DEFAULT_MODEL

    try:
        client = get_groq_client()
        prompt = build_explanation_prompt(topics)

        logger.info(f"Sending {len(topics)} topics to Groq ({model})...")

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a knowledgeable, friendly teacher who explains "
                        "complex topics in simple, beginner-friendly language."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=2048,
        )

        raw_response = chat_completion.choices[0].message.content
        logger.info("LLM explanation received successfully.")

        return {
            "raw_response": raw_response,
            "model_used": model,
            "topics_explained": topics
        }

    except EnvironmentError:
        raise
    except Exception as e:
        raise RuntimeError(f"LLM explanation failed: {str(e)}") from e
