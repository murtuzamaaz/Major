"""Code assist API endpoints with semantic code search."""

from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel

from backend.app.services.code_assist.improved_ingestion_service import (
    ingest_repository_from_path,
)
from backend.app.services.code_assist.improved_query_service import ask_question

router = APIRouter(prefix="/code-assist", tags=["Code Assist"])

# ── Path anchoring ────────────────────────────────────────────────────────────
# This file:  <project_root>/backend/app/routers/code_assist.py
#   parents[0] = backend/app/routers
#   parents[1] = backend/app
#   parents[2] = backend
#   parents[3] = <project_root>          ← same anchor as main.py's parent
#
# repo_fetcher.py: <project_root>/backend/app/services/repo_fetcher.py
#   parents[3] = <project_root>          ← identical
#
# Both resolve to <project_root>/data/repos — confirmed consistent.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = _PROJECT_ROOT / "data" / "repos"
_VECTOR_INDEX_ROOT = _PROJECT_ROOT / "data" / "vector_index"


class QueryRequest(BaseModel):
    """Request to query about the codebase."""
    question: str
    model: str = "deepseek-coder:6.7b"


@router.post("/index/{repo_id}")
def index_repo(repo_id: str):
    """
    Index a repository for semantic code search.

    The repository must first be uploaded via POST /upload_repo.
    Steps:
      1. Extracts project metadata and README
      2. Chunks all code files semantically (function/class boundaries)
      3. Generates enriched embeddings
      4. Stores in FAISS vector database
    """
    repo_path = _REPO_ROOT / repo_id

    if not repo_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Repository '{repo_id}' not found.",
                "looked_in": str(repo_path),
                "tip": (
                    "Make sure you called POST /upload_repo first, and that "
                    "your Docker volume is mounted so files persist between requests. "
                    "Check GET /health/storage to verify paths inside the container."
                ),
            },
        )

    try:
        result = ingest_repository_from_path(repo_id, str(repo_path))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask/{repo_id}")
def ask_about_code(repo_id: str, request: QueryRequest):
    """
    Ask questions about an indexed repository using multi-stage semantic retrieval.
    """
    try:
        result = ask_question(repo_id, request.question, request.model)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos")
def list_indexed_repos():
    """List all repositories that have been indexed."""
    from backend.app.services.code_assist.improved_vector_store_service import list_indexed_repos

    repos = list_indexed_repos()
    return {"count": len(repos), "repositories": repos}


@router.get("/stats/{repo_id}")
def get_repo_stats(repo_id: str):
    """Get indexing statistics for a repository."""
    from backend.app.services.code_assist.improved_vector_store_service import get_index_stats

    try:
        stats = get_index_stats(repo_id)
        return stats
    except Exception:
        raise HTTPException(status_code=404, detail=f"No index found for '{repo_id}'")


@router.get("/projects")
def list_indexed_projects():
    """
    Return all repositories that already have a vector index.
    Users can query these directly without re-indexing.
    """
    if not _VECTOR_INDEX_ROOT.exists():
        return {"count": 0, "projects": []}

    try:
        projects = [
            {"repo_id": d.name, "indexed": True}
            for d in _VECTOR_INDEX_ROOT.iterdir()
            if d.is_dir()
        ]
        return {"count": len(projects), "projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))