
import os
from pathlib import Path
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Centralized configuration for Land Intelligence AI."""

    # ================= PROJECT PATHS =================

    PROJECT_ROOT: Path = PROJECT_ROOT
    UPLOADS_DIR: Path = PROJECT_ROOT / "uploads"
    PROCESSING_STATE_FILE: Path = PROJECT_ROOT / "processing_state.json"

    # ================= GEMINI API =================
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    

    # Embedding
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "gemini-embedding-001"
    )
    EMBEDDING_DIMENSIONS: int = int(
        os.getenv("EMBEDDING_DIMENSIONS", "768")
    )
    EMBEDDING_MAX_INPUT_TOKENS: int = 8192

    # Chat LLM
    CHAT_MODEL: str = os.getenv("CHAT_MODEL", "openai/gpt-oss-120b")

    GROQ_MODEL: str = os.getenv("GROQ_MODEL", CHAT_MODEL)
    MISTRAL_MODEL: str = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    FALLBACK_MODELS: list[str] = [
        model.strip()
        for model in os.getenv("FALLBACK_MODELS", "").split(",")
        if model.strip()
    ]
    GEMINI_FALLBACK_MODELS: list[str] = FALLBACK_MODELS

    # ================= API RATE LIMITING =================

    GEMINI_RPM: int = int(os.getenv("GEMINI_RPM", "80"))
    GEMINI_TPM: int = int(os.getenv("GEMINI_TPM", "24000"))
    GEMINI_RPD: int = int(os.getenv("GEMINI_RPD", "800"))

    # Batch processing
    EMBEDDING_BATCH_SIZE: int = int(
        os.getenv("EMBEDDING_BATCH_SIZE", "50")
    )
    INGESTION_BATCH_SIZE: int = int(
        os.getenv("INGESTION_BATCH_SIZE", "50")
    )
    MAX_CONCURRENCY: int = int(
        os.getenv("MAX_CONCURRENCY", "1")
    )
    RATE_LIMIT_DELAY: float = float(
        os.getenv("RATE_LIMIT_DELAY", "60.0")
    )

    # Exponential backoff
    BACKOFF_INITIAL_WAIT: float = 60.0
    BACKOFF_MAX_WAIT: float = 240.0
    BACKOFF_MULTIPLIER: float = 2.0
    BACKOFF_MAX_RETRIES: int = 3

    # ================= DATABASE =================

    SUPABASE_DB_URL: str = os.getenv("SUPABASE_DB_URL", "")
    DATABASE_URL: str = SUPABASE_DB_URL

    VECTOR_TABLE: str = "land_documents"

    # ================= DOCUMENT PROCESSING =================

    CHUNK_SIZE_TOKENS: int = int(
        os.getenv("CHUNK_SIZE_TOKENS", "1000")
    )
    CHUNK_OVERLAP_TOKENS: int = int(
        os.getenv("CHUNK_OVERLAP_TOKENS", "200")
    )

    EXCEL_READINGS_PER_CHUNK: int = int(
        os.getenv("EXCEL_READINGS_PER_CHUNK", "50")
    )

    # ================= RAG CONFIGURATION =================

    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))

    RAG_SIMILARITY_THRESHOLD: float = float(
        os.getenv("RAG_SIMILARITY_THRESHOLD", "0.4")
    )

    # ================= FASTAPI =================

    APP_TITLE: str = "Land Intelligence AI (LIA)"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # ================= VALIDATION =================

    @classmethod
    def validate(cls) -> list[str]:
        errors = []

        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is missing.")

        if not cls.SUPABASE_DB_URL:
            errors.append("SUPABASE_DB_URL is missing.")

        return errors


# Singleton
settings = Settings()
