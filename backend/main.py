"""
FastAPI Application — PDF RAG Chatbot with LangGraph + LLMOps

API Endpoints:
  POST /upload           → Upload PDF, returns session_id
  POST /ask              → Ask a question (needs session_id)
  GET  /sessions         → List active sessions
  DELETE /session/{id}   → Delete a session
  GET  /history/{id}     → Get chat history for a session
  POST /feedback         → Submit thumbs up/down feedback
  GET  /feedback/{id}    → Get feedback for a session
  GET  /feedback-stats   → Aggregate feedback statistics
  GET  /                 → Serve frontend
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import logging
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower()
logger.info(f"Starting in {ENVIRONMENT} mode")

# ─── Lifespan Event Handlers ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    logger.info("Validating environment variables...")
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_key:
        logger.warning("GROQ_API_KEY environment variable is not set! The /ask endpoint will fail.")
    else:
        logger.info(f"GROQ_API_KEY is configured (key length: {len(groq_key)} chars)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down gracefully...")

# ─── FastAPI App Initialization ───────────────────────────────────────────────
app = FastAPI(
    title="PDF RAG Chatbot",
    description="Upload a PDF and ask questions using LangGraph hybrid search pipeline + LLMOps.",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for {request.client.host}")
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."}
    )

# ─── CORS Configuration ───────────────────────────────────────────────────────
cors_origins_env = os.getenv("CORS_ORIGINS", "https://internshi23.netlify.app,https://internship-project-1-ucof.onrender.com,http://localhost:5173,http://localhost:8000")
cors_origins_env = " ".join(cors_origins_env.split())  # Clean whitespace
cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health Check Endpoint ────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": ENVIRONMENT
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check - verifies API is fully operational."""
    try:
        engine = get_rag_engine()
        return {
            "ready": True,
            "active_sessions": len(engine.sessions) if hasattr(engine, 'sessions') else 0
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={"ready": False, "error": str(e)}
        )

# Lazy import: rag_engine pulls in ML dependencies; delaying it speeds up server startup.
_rag_engine = None

def get_rag_engine():
    global _rag_engine
    if _rag_engine is None:
        import rag_engine as _module
        _rag_engine = _module
    return _rag_engine

# Serve static files from the React build directory if it exists
if os.path.isdir("frontend/dist/assets"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


# ─── Request/Response Models ─────────────────────────────────────────────────
class AskRequest(BaseModel):
    session_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    source_chunks: list
    expanded_query: str
    session_id: str
    graph_metadata: dict = {}



# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the main HTML page from React build."""
    if os.path.exists("frontend/dist/index.html"):
        logger.info("Serving frontend from dist")
        return FileResponse("frontend/dist/index.html")
    logger.warning("Frontend not built - index.html not found")
    return JSONResponse(
        status_code=503,
        content={"error": "Frontend not built yet. Run 'npm run build' inside frontend/"}
    )


@app.post("/upload")
@limiter.limit("5/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    """
    Upload a PDF file (max 5 requests/minute).
    The PDF will be:
      1. Extracted (text from each page)
      2. Chunked (split into small pieces)
      3. Indexed (FAISS + BM25 hybrid search via LangGraph)
    Returns a session_id for asking questions.
    """
    if not file.filename:
        logger.warning("Upload attempt with no filename")
        raise HTTPException(status_code=400, detail="Filename is required.")
    
    if not file.filename.lower().endswith(".pdf"):
        logger.warning(f"Upload attempt with non-PDF file: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    try:
        pdf_bytes = await file.read()
        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        # Limit file size to 50MB
        max_size = 50 * 1024 * 1024
        if len(pdf_bytes) > max_size:
            raise HTTPException(status_code=413, detail=f"File too large. Maximum size: 50MB")
        
        logger.info(f"Processing PDF: {file.filename} ({len(pdf_bytes)} bytes)")
        result = get_rag_engine().create_session(pdf_bytes, file.filename)
        logger.info(f"Session created: {result['session_id']}")
        return result

    except ValueError as e:
        logger.error(f"Validation error during PDF upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing PDF. Please try again.")


@app.post("/ask")
@limiter.limit("10/minute")
async def ask_question(request: Request, data: AskRequest):
    """
    Ask a question about the uploaded PDF (max 10 requests/minute).
    Uses the LangGraph RAG pipeline:
      1. retrieve (hybrid BM25 + FAISS)
      2. grade_documents (relevance check)
      3. generate (LLM response)
    """
    if not data.question or not data.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    if len(data.question) > 5000:
        raise HTTPException(status_code=400, detail="Question too long (max 5000 chars).")
    
    if not data.session_id or not data.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID is required.")

    try:
        logger.info(f"Processing question for session {data.session_id}")
        result = get_rag_engine().ask_question(data.session_id, data.question)
        return result

    except ValueError as e:
        logger.warning(f"Session not found: {data.session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error during question processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing your question. Please try again.")


@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    try:
        sessions = get_rag_engine().get_sessions()
        logger.info(f"Listed {len(sessions)} active sessions")
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving sessions.")


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and free its memory."""
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID is required.")
    
    try:
        if get_rag_engine().delete_session(session_id):
            logger.info(f"Session deleted: {session_id}")
            return {"message": f"Session {session_id} deleted successfully."}
        else:
            logger.warning(f"Session not found for deletion: {session_id}")
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting session.")


@app.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get chat history for a session."""
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID is required.")
    
    try:
        history = get_rag_engine().get_chat_history(session_id)
        logger.info(f"Retrieved history for session {session_id} ({len(history)} messages)")
        return {"history": history, "session_id": session_id, "count": len(history)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving chat history.")



# ─── Run Server ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting PDF RAG Chatbot v2.0 (LangGraph + LLMOps)")
    port = int(os.getenv("PORT", "8000"))
    log_level = "info" if ENVIRONMENT == "production" else "debug"
    logger.info(f"Listening on http://0.0.0.0:{port}")
    
    # Use import string for reload support
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=ENVIRONMENT == "development",
        log_level=log_level,
        access_log=ENVIRONMENT == "development"
    )
