"""
PostgreSQL (Supabase) integration layer.
Drop-in replacement for snowflake_service.py.
Uses direct Postgres connection via psycopg2.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
from collections import Counter
from threading import Lock

import psycopg2
from psycopg2.extras import execute_values

from backend.app.core.settings import get_settings

# -----------------------------------------------------------------------------
# Connection handling (lazy, thread-safe)
# -----------------------------------------------------------------------------

_conn = None
_lock = Lock()


def _get_conn():
    global _conn

    if _conn is not None:
        return _conn

    with _lock:
        if _conn is not None:
            return _conn

        settings = get_settings()

        if not all([
            settings.supabase_db_host,
            settings.supabase_db_name,
            settings.supabase_db_user,
            settings.supabase_db_password,
        ]):
            raise RuntimeError("Supabase Postgres DB_* env vars are not fully configured")

        _conn = psycopg2.connect(
            host=settings.supabase_db_host,
            dbname=settings.supabase_db_name,
            user=settings.supabase_db_user,
            password=settings.supabase_db_password,
            port=settings.supabase_db_port or 5432,
        )
        _conn.autocommit = True
        return _conn


# -----------------------------------------------------------------------------
# Compatibility shim
# -----------------------------------------------------------------------------

def init_snowflake():
    return True


# -----------------------------------------------------------------------------
# Write operations
# -----------------------------------------------------------------------------

def store_simulation_run(repo_id: str, run_id: str, summary: Dict[str, Any]) -> bool:
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO simulation_runs (repo_id, run_id, overall_severity, timestamp)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    repo_id,
                    run_id,
                    summary.get("overall_severity", "unknown"),
                    summary.get("timestamp"),
                ),
            )
        return True
    except Exception:
        return False


def store_affected_files(repo_id: str, run_id: str, file_list: Iterable[Any]) -> bool:
    rows = []

    for entry in file_list:
        if isinstance(entry, dict):
            file_path = entry.get("file_path") or entry.get("path")
            if not file_path:
                continue
            rows.append(
                (
                    repo_id,
                    run_id,
                    file_path,
                    entry.get("severity", "unknown"),
                )
            )

    if not rows:
        return True

    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO affected_files (repo_id, run_id, file_path, severity)
                VALUES %s
                """,
                rows,
            )
        return True
    except Exception:
        return False


def store_ai_insight(repo_id: str, run_id: str, insight: str) -> bool:
    if not insight:
        return False

    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ai_insights (repo_id, run_id, insight)
                VALUES (%s, %s, %s)
                """,
                (repo_id, run_id, insight),
            )
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# Read helpers
# -----------------------------------------------------------------------------

def _build_report_payload(repo_id: str, run_row: tuple) -> Dict[str, Any]:
    run_id, overall_severity, created_at = run_row


    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT file_path, severity
            FROM affected_files
            WHERE repo_id = %s AND run_id = %s
            """,
            (repo_id, run_id),
        )
        files = cur.fetchall()

        cur.execute(
            """
            SELECT insight
            FROM ai_insights
            WHERE repo_id = %s AND run_id = %s
            LIMIT 1
            """,
            (repo_id, run_id),
        )
        insight_row = cur.fetchone()

    severity_counter = Counter()
    affected_files = []

    for file_path, severity in files:
        affected_files.append(file_path)
        severity_counter[(severity or "unknown").lower()] += 1

    summary = {"overall_severity": overall_severity}
    for sev, count in severity_counter.items():
        summary[f"{sev}_steps"] = count

    summary["affected_files"] = sorted(set(affected_files))

    return {
    "repo_id": repo_id,
    "run_id": run_id,
    "summary": summary,
    "ai_insight": insight_row[0] if insight_row else None,
    "timestamp": created_at,
    }



# -----------------------------------------------------------------------------
# Read operations
# -----------------------------------------------------------------------------
def fetch_latest_simulation_report(repo_id: str):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT run_id, overall_severity, created_at
            FROM simulation_runs
            WHERE repo_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (repo_id,),
        )
        row = cur.fetchone()

    if not row:
        return None

    return _build_report_payload(repo_id, row)




def fetch_simulation_report(repo_id: str, run_id: str):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT run_id, overall_severity, created_at
            FROM simulation_runs
            WHERE repo_id = %s AND run_id = %s
            LIMIT 1
            """,
            (repo_id, run_id),
        )
        row = cur.fetchone()

    if not row:
        return None

    return _build_report_payload(repo_id, row)



def fetch_severity_summary() -> Dict[str, int]:
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT LOWER(COALESCE(overall_severity, 'unknown')), COUNT(*)
            FROM simulation_runs
            GROUP BY 1
            """
        )
        rows = cur.fetchall()

    summary = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for sev, count in rows:
        if sev in summary:
            summary[sev] = count

    return summary


__all__ = [
    "init_snowflake",
    "store_simulation_run",
    "store_affected_files",
    "store_ai_insight",
    "fetch_latest_simulation_report",
    "fetch_simulation_report",
    "fetch_severity_summary",
]
