
import asyncio
import logging
from pathlib import Path
from typing import Callable, Coroutine, Any

from app.core.config import settings
from app.ai.rag.embed import embedding

logger = logging.getLogger("uvicorn.error")


class BatchProcessor:

    def __init__(
        self,
        embedding_batch_size: int = settings.EMBEDDING_BATCH_SIZE,
        ingestion_batch_size: int = settings.INGESTION_BATCH_SIZE,
        max_concurrency: int = settings.MAX_CONCURRENCY,
        rate_limit_delay: float = settings.RATE_LIMIT_DELAY,
    ):
        self.embedding_batch_size = embedding_batch_size
        self.ingestion_batch_size = ingestion_batch_size
        self.max_concurrency = max_concurrency
        self.rate_limit_delay = rate_limit_delay

    @staticmethod
    def chunk_list(items: list, size: int) -> list[list]:
        size = max(1, size)
        return [items[i:i + size] for i in range(0, len(items), size)]

    async def embed_chunks_batched(
        self,
        chunks: list[dict] | list[str],
        batch_size: int | None = None,
        rate_limit_delay: float | None = None,
        **kwargs,
    ) -> list[list[float]]:

        if not chunks:
            return []

        chunk_texts = [
            c["text"] if isinstance(c, dict) else c
            for c in chunks
        ]

        batch_size = batch_size or self.embedding_batch_size
        delay = rate_limit_delay if rate_limit_delay is not None else self.rate_limit_delay

        batches = self.chunk_list(chunk_texts, batch_size)
        total_batches = len(batches)

        all_embeddings = []

        logger.info("=" * 50)
        logger.info("EMBEDDING BATCH PROCESSING STARTED")
        logger.info(f"Total chunks      : {len(chunk_texts)}")
        logger.info(f"Batch size        : {batch_size}")
        logger.info(f"Total batches     : {total_batches}")
        logger.info("=" * 50)

        for index, batch in enumerate(batches, start=1):

            logger.info(
                f"[Embedding Batch {index}/{total_batches}] "
                f"Processing {len(batch)} chunks..."
            )

            embeddings = await embedding.embed_chunks(
                batch,
                batch_size=len(batch)
            )

            all_embeddings.extend(embeddings)

            logger.info(
                f"[Embedding Batch {index}/{total_batches}] "
                f"Completed: {len(embeddings)} embeddings generated"
            )

            if delay > 0 and index < total_batches:
                await asyncio.sleep(delay)

        logger.info("EMBEDDING BATCH PROCESSING COMPLETED")
        logger.info(f"Total embeddings generated: {len(all_embeddings)}")

        return all_embeddings

    async def process_ingestion_batches(
        self,
        files: list[Path],
        ingest_func: Callable[[Path], Coroutine[Any, Any, dict]],
        batch_size: int | None = None,
        max_concurrency: int | None = None,
        rate_limit_delay: float | None = None,
    ) -> list[dict]:

        if not files:
            return []

        batch_size = batch_size or self.ingestion_batch_size
        concurrency = (
            self.max_concurrency
            if max_concurrency is None
            else max_concurrency
        )
        delay = rate_limit_delay if rate_limit_delay is not None else self.rate_limit_delay

        semaphore = asyncio.Semaphore(concurrency)
        batches = self.chunk_list(files, batch_size)

        total_batches = len(batches)
        all_results = []

        logger.info("=" * 50)
        logger.info("DOCUMENT INGESTION STARTED")
        logger.info(f"Total files       : {len(files)}")
        logger.info(f"Batch size        : {batch_size}")
        logger.info(f"Total batches     : {total_batches}")
        logger.info(f"Max concurrency   : {concurrency}")
        logger.info("=" * 50)

        async def ingest_single(file_path: Path):
            async with semaphore:
                try:
                    result = await ingest_func(file_path)
                    return {"file": file_path.name, **result}

                except Exception as e:
                    logger.exception(f"Failed to ingest {file_path.name}")
                    return {
                        "file": file_path.name,
                        "status": "failed",
                        "message": str(e),
                        "document": None
                    }

        for index, batch in enumerate(batches, start=1):

            logger.info(
                f"[Ingestion Batch {index}/{total_batches}] "
                f"Processing {len(batch)} files..."
            )

            results = await asyncio.gather(
                *(ingest_single(file) for file in batch)
            )

            all_results.extend(results)

            successful = sum(
                1 for result in results
                if result.get("status") != "failed"
            )

            logger.info(
                f"[Ingestion Batch {index}/{total_batches}] "
                f"Completed: {successful}/{len(batch)} successful"
            )

            if delay > 0 and index < total_batches:
                await asyncio.sleep(delay)

        logger.info("DOCUMENT INGESTION COMPLETED")
        logger.info(f"Total files processed: {len(all_results)}")

        return all_results


batch_processor = BatchProcessor()

