
import logging
from collections.abc import AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

from langchain_core.messages import HumanMessage

from app.core.config import settings

logger = logging.getLogger("lia")


class ModelRegistry:
    """Manages LangChain LLM providers with fallback and retry."""

    def __init__(self):
        self.models = self._initialize_models()
        self.llm = self._build_fallback_chain()

    def _initialize_models(self) -> list[tuple[str, BaseChatModel]]:
        candidates = []

        if settings.GROQ_API_KEY:
            candidates.append((
                "Groq",
                ChatGroq(
                    model=settings.GROQ_MODEL,
                    api_key=settings.GROQ_API_KEY,
                    temperature=0.3,
                )
            ))

        if settings.MISTRAL_API_KEY:
            candidates.append((
                "Mistral",
                ChatMistralAI(
                    model=settings.MISTRAL_MODEL,
                    api_key=settings.MISTRAL_API_KEY,
                    temperature=0.3,
                )
            ))

        if settings.GEMINI_API_KEY:
            candidates.append((
                "Gemini",
                ChatGoogleGenerativeAI(
                    model=settings.GEMINI_MODEL,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=0.3,
                )
            ))

        if not candidates:
            raise ValueError("No LLM provider API keys are configured.")

        return candidates

    def _build_fallback_chain(self) -> Runnable:
        """Builds retry-enabled models and a fallback chain."""

        retry_models = []

        for provider, model in self.models:
            retry_model = model.with_retry(
                retry_if_exception_type=(Exception,),
                stop_after_attempt=3,
                wait_exponential_jitter=True,
            )

            retry_models.append((provider, retry_model))

        primary_provider, primary_model = retry_models[0]

        fallback_models = [
            model for _, model in retry_models[1:]
        ]

        if fallback_models:
            return primary_model.with_fallbacks(
                fallback_models,
                exceptions_to_handle=(Exception,),
            )

        return primary_model

    async def generate(self, prompt: str) -> str:
        """Generates a complete response with retry and fallback."""

        try:
            response = await self.llm.ainvoke(
                [HumanMessage(content=prompt)]
            )

            return response.content

        except Exception as error:
            logger.error("All LLM providers failed: %s", error)
            raise RuntimeError(
                "All configured LLM providers failed."
            ) from error

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        """Streams response chunks."""

        async for chunk in self.llm.astream(
            [HumanMessage(content=prompt)]
        ):
            if chunk.content:
                if isinstance(chunk.content, str):
                    yield chunk.content


models = ModelRegistry()
