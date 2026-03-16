"""
topic_extractor.py

Extracts key topics from a transcript using a two-stage approach:
  1. LLM-based extraction (Groq) — primary, works well on conversational speech
  2. KeyBERT fallback — used only if LLM extraction fails
"""

import os
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def extract_topics_with_llm(transcript: str, top_n: int = 7) -> List[str]:
    """Use Groq LLM to extract meaningful topics from a transcript."""
    from groq import Groq
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY not set.")

    client = Groq(api_key=api_key)

    prompt = f"""You are an expert at analyzing educational video transcripts.

Read the following transcript carefully and extract the {top_n} most important technical or conceptual topics that are actually discussed or mentioned in it.

Rules:
- Extract ONLY real topics that appear in the transcript (e.g. "LLM", "Context Window", "API", "Prompt Engineering")
- Each topic should be a clean 1-3 word phrase
- Do NOT include filler words, names, or generic words like "video", "things", "stuff"
- Return ONLY a numbered list, one topic per line, nothing else
- Example format:
1. Large Language Models
2. Context Window
3. API Integration

Transcript:
\"\"\"{transcript}\"\"\"

Return only the numbered list:"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()

    topics = []
    seen = set()
    for line in raw.splitlines():
        line = line.strip()
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', line).strip()
        cleaned = re.sub(r'[*_`]', '', cleaned).strip()
        if cleaned and cleaned.lower() not in seen and len(cleaned) > 2:
            seen.add(cleaned.lower())
            topics.append(cleaned)

    logger.info(f"LLM extracted {len(topics)} topics: {topics}")
    return topics[:top_n]


_kw_model = None

def get_kw_model():
    global _kw_model
    if _kw_model is None:
        from keybert import KeyBERT
        logger.info("Loading KeyBERT model (fallback)...")
        _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
        logger.info("KeyBERT model loaded.")
    return _kw_model


def extract_topics_with_keybert(transcript: str, top_n: int = 7) -> List[str]:
    """KeyBERT fallback."""
    model = get_kw_model()
    keywords = model.extract_keywords(
        transcript,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        use_mmr=True,
        diversity=0.5,
        top_n=top_n
    )
    topics = []
    seen = set()
    for phrase, score in keywords:
        clean = re.sub(r'\s+', ' ', phrase).strip().title()
        if clean and clean.lower() not in seen:
            seen.add(clean.lower())
            topics.append(clean)
    return topics


def extract_topics(
    transcript: str,
    top_n: int = 7,
    ngram_range: tuple = (1, 2),
    diversity: float = 0.5
) -> List[str]:
    """
    Extract key topics — LLM first, KeyBERT as fallback.
    """
    cleaned = transcript.strip()
    if not cleaned:
        raise ValueError("Transcript is empty.")
    if len(cleaned.split()) < 5:
        raise ValueError("Transcript too short for topic extraction.")

    try:
        topics = extract_topics_with_llm(cleaned, top_n=top_n)
        if topics:
            return topics
        logger.warning("LLM returned empty topics, falling back to KeyBERT.")
    except Exception as e:
        logger.warning(f"LLM topic extraction failed ({e}), falling back to KeyBERT.")

    try:
        topics = extract_topics_with_keybert(cleaned, top_n=top_n)
        logger.info(f"KeyBERT fallback extracted {len(topics)} topics: {topics}")
        return topics
    except Exception as e:
        raise RuntimeError(f"Topic extraction failed: {str(e)}") from e