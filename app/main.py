"""
LIA - Land Intelligence AI Backend Application

Main FastAPI entry point with structured startup lifecycle:
1. Ping PostgreSQL (Supabase) to verify database connectivity.
2. Ensure pgvector extension and document/chunk tables exist.
3. Run data ingestion on the uploads directory (with SHA-256 hash deduplication).
4. Serve REST API endpoints for health checks and RAG chat.
"""

import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.pg_vector import ping_database
from app.ai.rag.vector_store import vector_store
from app.ai.rag.pipeline import rag_pipeline
from app.routes import chat

# Configure formatted logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("lia")
logger.setLevel(logging.INFO)

# uploads folder is located at the project root: <root>/uploads
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Context Manager.
    
    Code BEFORE 'yield' runs when the server starts up.
    Code AFTER 'yield' runs when the server shuts down.
    
    Startup Lifecycle Order:
    -----------------------
    1. Ping Test: Connect to PostgreSQL (Supabase) and test responsiveness.
    2. Schema Initialization: Ensure 'documents' and 'chunks' tables exist with vector support.
    3. Data Ingestion: Scan the uploads/ directory, check file hashes, and ingest new documents.
    """
    logger.info("=" * 60)
    logger.info("LIA SERVER STARTUP SEQUENCE INITIATED")
    logger.info("=" * 60)

    # ----------------------------------------------------
    # STEP 1: PostgreSQL Supabase Ping Test
    # ----------------------------------------------------
    logger.info("[STARTUP STEP 1/3] Running PostgreSQL Supabase ping test...")
    db_connected = ping_database()

    if db_connected:
        logger.info("[STARTUP STEP 1/3] PostgreSQL ping SUCCESSFUL! Database is ready.")

        # ----------------------------------------------------
        # STEP 2: Verify / Create Tables in Database
        # ----------------------------------------------------
        logger.info("[STARTUP STEP 2/3] Verifying database tables ('documents' and 'chunks')...")
        vector_store.create_tables_if_not_exist()

        # ----------------------------------------------------
        # STEP 3: Sequential Data Ingestion with Hash Deduplication
        # ----------------------------------------------------
        logger.info("[STARTUP STEP 3/3] Starting data ingestion from uploads folder...")
        await rag_pipeline.data_ingestion(UPLOADS_DIR)

    else:
        logger.warning("=" * 60)
        logger.warning("[STARTUP WARNING] Database ping failed or credentials not set.")
        logger.warning("Data ingestion is SKIPPED because the database is offline.")
        logger.warning("Please update your .env file with valid SUPABASE_DB_URL to enable full RAG features.")
        logger.warning("=" * 60)

    logger.info("=" * 60)
    logger.info("LIA SERVER READY - Listening for API requests")
    logger.info("=" * 60)

    # Application is now running and serving requests
    yield

    # Shutdown sequence
    logger.info("LIA SERVER SHUTTING DOWN...")


# Initialize the FastAPI application instance
app = FastAPI(
    title="Land Intelligence AI (LIA)",
    description="Intelligent RAG pipeline for land documents and geospatial analytics",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "https://lia-land-intelligence-ai.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def landing_page():
    """Simple root welcome endpoint."""
    return {
        "app": "Land Intelligence AI (LIA)",
        "status": "online",
        "message": "Welcome! Backend is running successfully."
    }


@app.get("/health")
def health():
    """
    Health check endpoint to verify server status.
    Can be polled by monitoring tools or frontend clients.
    """
    return {
        "status": "ok",
        "service": "LIA Backend"
    }


# Register chat and query routes
app.include_router(chat.router)
