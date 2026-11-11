
"""
LIA - Vector Store Module (PostgreSQL + pgvector)

This module handles:
1. Creating the 'documents' and 'chunks' tables in PostgreSQL/Supabase.
2. Checking if a document's SHA-256 hash already exists in the database (hash-based deduplication).
3. Inserting text chunks and their high-dimensional vector embeddings into pgvector.
4. Cosine/L2 similarity search to retrieve the most relevant chunks for user questions.
"""

import asyncio
import logging
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector

from app.core.config import settings
from app.utils.ids import generate_uuid

# Set up logger for clean, structured console output
logger = logging.getLogger("lia")
logger.setLevel(logging.INFO)


class VectorStore:
    """
    Manages vector database operations for document ingestion and semantic search.
    """

    def __init__(self):
        # We do NOT run database queries inside __init__ to avoid crashing
        # when the application imports this module before startup health checks.
        pass

    @property
    def db_url(self) -> str:
        """Helper to get the current database URL from centralized settings."""
        return settings.SUPABASE_DB_URL or settings.DATABASE_URL

    def create_tables_if_not_exist(self) -> bool:
        """
        Creates the 'documents' and 'chunks' tables in PostgreSQL if they do not exist already.

        Tables created:
        1. 'documents': Stores file-level metadata (filename, SHA-256 hash, upload timestamps).
           The 'file_hash' column has a UNIQUE constraint to prevent duplicate ingestion.
        2. 'chunks': Stores text chunks and their vector embeddings.
        """
        if not self.db_url:
            logger.warning("[DB] Cannot create tables: Database URL is not configured.")
            return False

        try:
            with psycopg.connect(self.db_url, connect_timeout=5) as connection:
                connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        file_hash TEXT UNIQUE NOT NULL,
                        file_size_bytes BIGINT,
                        uploaded_at TEXT,
                        ingested_at TEXT,
                        ingestion_status TEXT,
                        chunk_count INTEGER,
                        chunking_version TEXT,
                        embedding_model TEXT
                    );
                """)

                connection.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id TEXT PRIMARY KEY,
                        filename_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        chunk_index INTEGER,
                        page_number INTEGER,
                        text TEXT NOT NULL,
                        embedding_model_name TEXT,
                        embedding VECTOR
                    );
                """)

                connection.commit()

            logger.info("[DB SETUP] Tables 'documents' and 'chunks' verified / created successfully.")
            return True

        except Exception as error:
            logger.error(f"[DB SETUP ERROR] Failed to initialize tables: {error}")
            return False

    def get_connection(self):
        """
        Opens a connection to PostgreSQL configured to return dictionary rows
        and enables the pgvector vector type.
        """
        connection = psycopg.connect(
            self.db_url,
            row_factory=dict_row
        )
        register_vector(connection)
        logger.info(f"[DB CONNECTION] Using database: {self.db_url.split('@')[-1]}")
        return connection

    async def get_document_by_hash(self, file_hash: str) -> dict | None:
        """
        Checks if a file with this exact SHA-256 content hash has already been ingested.
        """
        if not self.db_url:
            return None

        def _get():
            try:
                with self.get_connection() as connection:
                    result = connection.execute("""
                        SELECT *
                        FROM documents
                        WHERE file_hash = %s
                        LIMIT 1;
                    """, (file_hash,)).fetchone()
                    return result
            except Exception as e:
                logger.warning(f"[DB QUERY] Could not check document hash: {e}")
                return None

        return await asyncio.to_thread(_get)

    async def get_document_by_id(self, document_id: str) -> dict | None:
        """Retrieves a document record by its primary key UUID."""
        def _get():
            with self.get_connection() as connection:
                return connection.execute("""
                    SELECT *
                    FROM documents
                    WHERE document_id = %s;
                """, (document_id,)).fetchone()

        return await asyncio.to_thread(_get)

    async def insert(
        self,
        document_record: dict,
        chunks: list[dict],
        embeddings: list[list[float]]
    ) -> None:
        """
        Stores document metadata and its embedded text chunks into PostgreSQL.
        """
        def _insert():
            if len(chunks) != len(embeddings):
                raise ValueError("Chunks and embeddings count mismatch")

            with self.get_connection() as connection:
                connection.execute("""
                    INSERT INTO documents (
                        document_id,
                        filename,
                        file_hash,
                        file_size_bytes,
                        uploaded_at,
                        ingested_at,
                        ingestion_status,
                        chunk_count,
                        chunking_version,
                        embedding_model
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (file_hash) DO NOTHING;
                """, (
                    document_record["document_id"],
                    document_record["filename"],
                    document_record["file_hash"],
                    document_record["file_size_bytes"],
                    document_record["uploaded_at"],
                    document_record["ingested_at"],
                    document_record["ingestion_status"],
                    document_record["chunk_count"],
                    document_record["chunking_version"],
                    document_record["embedding_model"]
                ))

                for chunk, vector in zip(chunks, embeddings):
                    connection.execute("""
                        INSERT INTO chunks (
                            id,
                            filename_id,
                            filename,
                            chunk_index,
                            page_number,
                            text,
                            embedding_model_name,
                            embedding
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        chunk.get("id") or generate_uuid(),
                        document_record["document_id"],
                        document_record["filename"],
                        int(chunk["chunk_index"]),
                        int(chunk["page_number"]),
                        chunk["text"],
                        document_record["embedding_model"],
                        vector
                    ))

                connection.commit()
                logger.info(
                    f"[DB INSERT] Successfully stored {len(chunks)} chunks "
                    f"for '{document_record['filename']}' in Supabase pgvector."
                )

        await asyncio.to_thread(_insert)

    async def retrieve(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        document_id: str | None = None
    ) -> list[dict]:
        """
        Queries the vector store using cosine distance (<=> operator in pgvector)
        to find the most relevant chunks matching the user's question embedding.
        """

        def _retrieve():
            with self.get_connection() as connection:

                if document_id:
                    results = connection.execute("""
                        SELECT *
                        FROM (
                            SELECT *,
                                   embedding <=> %s::vector AS distance
                            FROM chunks
                            WHERE filename_id = %s
                        ) AS ranked_chunks
                        WHERE distance <= %s
                        ORDER BY distance ASC
                        LIMIT %s;
                    """, (
                        query_embedding,
                        document_id,
                        settings.RAG_SIMILARITY_THRESHOLD,
                        n_results
                    )).fetchall()

                else:
                    results = connection.execute("""
                        SELECT *
                        FROM (
                            SELECT *,
                                   embedding <=> %s::vector AS distance
                            FROM chunks
                        ) AS ranked_chunks
                        WHERE distance <= %s
                        ORDER BY distance ASC
                        LIMIT %s;
                    """, (
                        query_embedding,
                        settings.RAG_SIMILARITY_THRESHOLD,
                        n_results
                    )).fetchall()

                return [
                    {
                        "id": row["id"],
                        "document": row["text"],
                        "metadata": {
                            "document_id": row["filename_id"],
                            "filename": row["filename"],
                            "chunk_index": row["chunk_index"],
                            "page_number": row["page_number"],
                            "embedding_model_name": row["embedding_model_name"]
                        },
                        "distance": row["distance"]
                    }
                    for row in results
                ]

        return await asyncio.to_thread(_retrieve)


# Singleton instance
vector_store = VectorStore()
