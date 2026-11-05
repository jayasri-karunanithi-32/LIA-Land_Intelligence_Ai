
import asyncio
import logging

from google import genai
from google.genai import types

from app.core.config import settings


logger = logging.getLogger(__name__)


class Embedding:

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL):
        self.model_name = model_name
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )
        self.max_retries = settings.BACKOFF_MAX_RETRIES

    async def _embed_with_retry(
        self,
        contents: str | list[str],
        task_type: str
    ) -> list[list[float]]:

        for attempt in range(self.max_retries + 1):

            try:
                result = await self.client.aio.models.embed_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=settings.EMBEDDING_DIMENSIONS
                    )
                )

                return [
                    item.values
                    for item in result.embeddings
                ]

            except Exception as e:

                error_message = str(e)

                is_rate_limit_error = (
                    "429" in error_message
                    or "RESOURCE_EXHAUSTED" in error_message
                )

                if not is_rate_limit_error:
                    logger.exception("Gemini embedding API error")
                    raise

                if attempt >= self.max_retries:
                    logger.error(
                        "Embedding failed after %s retries: %s",
                        self.max_retries,
                        error_message
                    )
                    raise

                backoff_time = min(
                    settings.BACKOFF_INITIAL_WAIT
                    * (settings.BACKOFF_MULTIPLIER ** attempt),
                    settings.BACKOFF_MAX_WAIT
                )

                wait_time = max(
                    settings.RATE_LIMIT_DELAY,
                    backoff_time
                )

                logger.warning(
                    "Gemini rate limit reached. "
                    "Waiting %.1f seconds before retry. "
                    "Attempt %s/%s",
                    wait_time,
                    attempt + 1,
                    self.max_retries
                )

                await asyncio.sleep(wait_time)

        return []

    async def embed_batch(
        self,
        chunks: list[str]
    ) -> list[list[float]]:

        if not chunks:
            return []

        return await self._embed_with_retry(
            contents=chunks,
            task_type="RETRIEVAL_DOCUMENT"
        )

    async def embed_chunks(
        self,
        chunks: list[str],
        batch_size: int | None = None
    ) -> list[list[float]]:

        if not chunks:
            return []

        all_embeddings = []

        batch_size = (
            settings.EMBEDDING_BATCH_SIZE
            if batch_size is None
            else max(1, batch_size)
        )

        for i in range(0, len(chunks), batch_size):

            batch = chunks[i:i + batch_size]

            logger.info(
                "Generating embeddings for %s chunks",
                len(batch)
            )

            embeddings = await self.embed_batch(batch)

            all_embeddings.extend(embeddings)

        return all_embeddings

    async def embed_query(
        self,
        prompt: str
    ) -> list[float]:

        if not prompt.strip():
            return []

        embeddings = await self._embed_with_retry(
            contents=prompt,
            task_type="RETRIEVAL_QUERY"
        )

        return embeddings[0] if embeddings else []


embedding = Embedding()
