
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


@dataclass
class RawDocument:
    """A single document extracted from a source file."""
    content: str
    metadata: dict[str, Any]
    source_file: str
    source_type: str
    doc_id: str = ""


@dataclass
class TextChunk:
    """A chunk of text ready for embedding."""
    content: str
    metadata: dict[str, Any]
    source_file: str
    source_type: str
    chunk_index: int
    total_chunks: int
    doc_id: str = ""
    chunk_id: str = ""
    estimated_tokens: int = 0


@dataclass
class EmbeddingResult:
    """Result of embedding a single chunk."""
    chunk: TextChunk
    embedding: list[float] = field(default_factory=list)
    success: bool = True
    error: str = ""


@dataclass
class BatchResult:
    """Result of processing a batch of chunks."""
    results: list[EmbeddingResult] = field(default_factory=list)
    total_tokens_used: int = 0
    api_calls_made: int = 0


@dataclass
class ProcessingState:
    """Tracks overall ingestion processing state."""
    processed_chunk_ids: set[str] = field(default_factory=set)
    failed_chunk_ids: set[str] = field(default_factory=set)
    total_documents: int = 0
    total_chunks: int = 0
    total_embedded: int = 0
    total_failed: int = 0
    last_updated: str = ""
    daily_requests_used: int = 0
    daily_reset_date: str = ""

    def to_dict(self) -> dict:
        return {
            "processed_chunk_ids": list(self.processed_chunk_ids),
            "failed_chunk_ids": list(self.failed_chunk_ids),
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "total_embedded": self.total_embedded,
            "total_failed": self.total_failed,
            "last_updated": self.last_updated,
            "daily_requests_used": self.daily_requests_used,
            "daily_reset_date": self.daily_reset_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProcessingState:
        return cls(
            processed_chunk_ids=set(data.get("processed_chunk_ids", [])),
            failed_chunk_ids=set(data.get("failed_chunk_ids", [])),
            total_documents=data.get("total_documents", 0),
            total_chunks=data.get("total_chunks", 0),
            total_embedded=data.get("total_embedded", 0),
            total_failed=data.get("total_failed", 0),
            last_updated=data.get("last_updated", ""),
            daily_requests_used=data.get("daily_requests_used", 0),
            daily_reset_date=data.get("daily_reset_date", ""),
        )


class ChatRequest(BaseModel):
    """Incoming chat request from the user."""
    query: str = Field(
        ..., min_length=1, max_length=2000,
        description="User's question"
    )
    top_k: int = Field(
        default=5, ge=1, le=20,
        description="Number of context documents to retrieve"
    )


class RetrievedDocument(BaseModel):
    """A document retrieved from the vector store."""
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_file: str = ""
    source_type: str = ""
    similarity_score: float = 0.0


class ChatResponse(BaseModel):
    """Response from the RAG chat system."""
    answer: str
    sources: list[RetrievedDocument] = Field(default_factory=list)
    query: str = ""


class IngestionStatus(BaseModel):
    """Status report for the ingestion pipeline."""
    status: str
    total_documents: int = 0
    total_chunks: int = 0
    total_embedded: int = 0
    total_failed: int = 0
    files_processed: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    message: str = ""


class ModelRegistry:
    """
    Manages LLM model candidates with streaming capabilities
    and fallback chains.
    """

    def __init__(self):
        self._gemini_client = None
        self._groq_client = None
        self._mistral_client = None
        self._nvidia_client = None

    # ================= GEMINI CLIENT =================

    def _get_gemini_client(self):
        if self._gemini_client is None:
            from google import genai
            from app.core.config import settings

            self._gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

        return self._gemini_client

    # ================= GROQ CLIENT =================

    def _get_groq_client(self):
        if self._groq_client is None:
            from groq import AsyncGroq
            from app.core.config import settings

            self._groq_client = AsyncGroq(
                api_key=settings.GROQ_API_KEY
            )

        return self._groq_client

    # ================= MISTRAL CLIENT =================

    def _get_mistral_client(self):
        if self._mistral_client is None:
            from mistralai import Mistral
            from app.core.config import settings

            self._mistral_client = Mistral(
                api_key=settings.MISTRAL_API_KEY
            )

        return self._mistral_client

    # ================= NVIDIA CLIENT =================

    def _get_nvidia_client(self):
        if self._nvidia_client is None:
            from openai import AsyncOpenAI
            from app.core.config import settings

            self._nvidia_client = AsyncOpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=settings.NVIDIA_API_KEY
            )

        return self._nvidia_client

    # ================= GROQ STREAMING =================

    async def stream_groq(self, prompt: str):
        """Streams text chunks from Groq API."""

        from app.core.config import settings

        client = self._get_groq_client()

        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )

        async for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                yield content

    # ================= MISTRAL STREAMING =================

    async def stream_mistral(self, prompt: str):
        """Streams text chunks from Mistral API."""

        from app.core.config import settings

        client = self._get_mistral_client()

        response = await client.chat.stream_async(
            model=settings.MISTRAL_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        async for event in response:
            if event.data and event.data.choices:
                content = event.data.choices[0].delta.content

                if content:
                    yield content

    # ================= NVIDIA STREAMING =================

    async def stream_nvidia(self, prompt: str):
        """Streams text chunks from NVIDIA API."""

        from app.core.config import settings

        client = self._get_nvidia_client()

        response = await client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )

        async for chunk in response:
            content = chunk.choices[0].delta.content

            if content:
                yield content

    # ================= GEMINI STREAMING =================

    async def stream_gemini(self, prompt: str):
        """Streams text chunks from Gemini API."""

        from app.core.config import settings

        client = self._get_gemini_client()

        response = await client.aio.models.generate_content_stream(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    # ================= FALLBACK CHAIN =================

    def get_fallback_chain(self) -> list[tuple[str, Any]]:
        """Returns ordered list of LLM providers."""

        return [
            ("Groq", self.stream_groq),
            ("Mistral", self.stream_mistral),
            ("NVIDIA", self.stream_nvidia),
            ("Gemini Flash", self.stream_gemini),
        ]


# ================= SINGLETON =================

models = ModelRegistry()
