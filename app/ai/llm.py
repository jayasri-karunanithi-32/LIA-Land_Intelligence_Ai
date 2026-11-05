"""
LIA - LLM Streaming & Fallback Module

Provides multi-model fallback streaming using Google Gemini via google-genai SDK.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Callable, Any

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Manages Gemini LLM requests with automatic fallback across configured models.
    """

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.primary_model = getattr(
            settings,
            "GEMINI_MODEL",
            getattr(settings, "CHAT_MODEL", "gemini-2.0-flash-lite")
        )

        self.fallback_models = getattr(
            settings,
            "GEMINI_FALLBACK_MODELS",
            []
        )

    async def stream_model(self, model: str, prompt: str) -> AsyncGenerator[str, None]:
        """Streams text chunks from a specific Gemini model."""
        response = await self.client.aio.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            ),
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def get_fallback_chain(self) -> list[tuple[str, Callable[[str], AsyncGenerator[str, None]]]]:
        """
        Returns a list of (model_name, streaming_function) tuples in priority order.
        ChatService iterates over these tuples to execute streaming with retry and jitter.
        """
        all_models = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        chain = []

        for model_name in all_models:
            def make_streamer(m: str):
                def streamer(prompt: str) -> AsyncGenerator[str, None]:
                    return self.stream_model(m, prompt)
                return streamer

            chain.append((model_name, make_streamer(model_name)))

        return chain

    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        """Convenience method to stream response through the fallback chain directly."""
        last_error = None

        for model_name, stream_func in self.get_fallback_chain():
            try:
                async for chunk in stream_func(prompt):
                    yield chunk
                return

            except Exception as exc:
                last_error = exc
                logger.warning("Gemini model %s failed: %s", model_name, exc)

        logger.error("All Gemini models failed: %s", last_error)
        raise RuntimeError("All configured Gemini models failed.") from last_error


# Singleton instance
models = LLMService()
