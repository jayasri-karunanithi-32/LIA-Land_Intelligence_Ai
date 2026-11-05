"""
LIA - RAG Ingestion & Retrieval Pipeline

This module coordinates:
1. Scanning documents in the uploads folder.
2. Checking document SHA-256 hashes against PostgreSQL/Supabase to skip duplicates.
3. Parsing new files into overlapping text chunks.
4. Generating vector embeddings using Google Gemini API.
5. Storing chunks and vectors in the database.
6. Semantic retrieval for answering user queries.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from app.ai.rag.data_loader import data_processor
from app.ai.rag.embed import embedding
from app.ai.rag.vector_store import vector_store
from app.ai.rag.batch_processing import batch_processor
from app.utils.ids import generate_uuid

# Set up logging for clear, formatted messages in the terminal
logger = logging.getLogger("lia")
logger.setLevel(logging.INFO)


class RagPipeline:
    """
    Orchestrates end-to-end document ingestion and semantic search.
    """

    @staticmethod
    async def ingest_file(path: str | Path, batch_size: int | None = None) -> dict:
        """
        Ingests a single file into the vector database.

        Sequential steps:
        1. Compute SHA-256 hash of the file bytes.
        2. Query PostgreSQL to see if this hash already exists.
           -> If it exists: SKIP immediately (no re-embedding, saving time & API quota).
        3. Parse the file into text pages and create text chunks.
        4. Generate embeddings via the Gemini Embedding API.
        5. Save metadata into the 'documents' table and vectors into the 'chunks' table.
        """
        path = Path(path)
        uploaded_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Compute file hash for deduplication
        file_hash = data_processor.compute_hash(path)
        logger.info(f"[HASH CHECK] Checking '{path.name}' (SHA-256: {file_hash[:12]}...)")

        # Step 2: Check database for existing document with the same content hash
        existing_doc = await vector_store.get_document_by_hash(file_hash)
        if existing_doc:
            logger.info(
                f"[SKIPPED] File '{path.name}' was already ingested as '{existing_doc.get('filename')}' "
                f"on {existing_doc.get('ingested_at')}. Skipping to avoid duplicate records."
            )
            return {
                "status": "skipped",
                "message": f"File '{path.name}' already ingested as '{existing_doc.get('filename')}'.",
                "document": existing_doc
            }

        logger.info(f"[INGESTING] File '{path.name}' is new. Parsing text content...")

        # Step 3: Process file, extract text per page and split into chunks
        content = await data_processor.process_file(path)
        chunks = content.get("chunks", [])
        if not chunks:
            logger.warning(f"[EMPTY] File '{path.name}' contains no extractable text.")
            return {
                "status": "empty",
                "message": f"File '{path.name}' has no extractable text.",
                "document": None
            }

        logger.info(f"[CHUNKING] '{path.name}' split into {len(chunks)} chunks. Generating embeddings...")

        # Step 4: Generate embeddings for all chunks in batches
        embeddings = await batch_processor.embed_chunks_batched(chunks, batch_size=batch_size)

        # Step 5: Construct Document Record
        document_id = generate_uuid()
        ingested_at = datetime.now(timezone.utc).isoformat()
        document_record = {
            "document_id": document_id,
            "filename": content["filename"],
            "file_hash": file_hash,
            "file_size_bytes": content["file_size_bytes"],
            "uploaded_at": uploaded_at,
            "ingested_at": ingested_at,
            "ingestion_status": "completed",
            "chunk_count": content["total_chunks"],
            "chunking_version": "v1",
            "embedding_model": embedding.model_name
        }

        # Step 6: Insert into PostgreSQL / Supabase pgvector
        await vector_store.insert(
            document_record=document_record,
            chunks=chunks,
            embeddings=embeddings
        )

        logger.info(f"[COMPLETED] Successfully ingested '{path.name}' with {len(chunks)} chunks.")

        return {
            "status": "completed",
            "message": f"File '{path.name}' ingested with {content['total_chunks']} chunks.",
            "document": document_record
        }

    @staticmethod
    async def data_ingestion(folder_path: str | Path = "uploads", batch_size: int | None = None) -> dict:
        """
        Scans a folder and ingests all supported files (.pdf, .txt, .md).
        Files whose content hash already exists in PostgreSQL are automatically skipped.
        """
        logger.info("=" * 60)
        logger.info(f"[DATA INGESTION] Scanning folder: {Path(folder_path).resolve()}")

        files = data_processor.list_files(folder_path)
        summary = {
            "total": len(files),
            "ingested": 0,
            "skipped": 0,
            "failed": 0,
            "results": []
        }

        if not files:
            logger.info(f"[DATA INGESTION] No documents found in '{folder_path}'. Place files here to ingest.")
            logger.info("=" * 60)
            return summary

        logger.info(f"[DATA INGESTION] Found {len(files)} document(s) to process.")

        # Process document ingestion in batches
        results = await batch_processor.process_ingestion_batches(
            files,
            RagPipeline.ingest_file,
            batch_size=batch_size
        )

        for result in results:
            status = result.get("status")
            if status == "completed":
                summary["ingested"] += 1
            elif status == "failed":
                summary["failed"] += 1
            else:
                summary["skipped"] += 1

            summary["results"].append(result)

        logger.info("=" * 60)
        logger.info(
            f"[DATA INGESTION SUMMARY] Total: {summary['total']} | "
            f"Ingested: {summary['ingested']} | "
            f"Skipped: {summary['skipped']} | "
            f"Failed: {summary['failed']}"
        )
        logger.info("=" * 60)
        return summary

    @staticmethod
    async def retrieve(query: str, n_results: int = 5, document_id: str | None = None) -> dict:
        """Retrieves top matching chunks from the vector store for a user prompt."""
        query_embedding = await embedding.embed_query(query)
        results = await vector_store.retrieve(
            query_embedding=query_embedding,
            n_results=n_results,
            document_id=document_id
        )

        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }

    @staticmethod
    def build_context(results: list[dict]) -> tuple[str, list[dict]]:
        """Formats retrieved chunks into a context string for the LLM prompt."""
        context_blocks = []
        sources = []
        seen = set()

        for result in results:
            meta = result.get("metadata") or {}
            filename = meta.get("filename", "unknown")
            page_number = meta.get("page_number")

            context_blocks.append(f"[Source: {filename}, page {page_number}]\n{result['document']}")

            if (filename, page_number) not in seen:
                seen.add((filename, page_number))
                sources.append({
                    "filename": filename,
                    "page_number": page_number,
                    "distance": result.get("distance")
                })

        return "\n\n".join(context_blocks), sources


# Singleton pipeline instance
rag_pipeline = RagPipeline()
