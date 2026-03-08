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

def store_performance_run(repo_id: str, run_id: str, data: Dict[str, Any]) -> bool:
    try:
        conn = _get_conn()

        metrics = data.get("metrics", {})
        req = metrics.get("requests", {})
        rt = metrics.get("response_time", {})
        vus = metrics.get("virtual_users", {})

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO performance_runs (
                    repo_id,
                    run_id,
                    target_url,
                    test_type,
                    duration,
                    vus_max,
                    vus_avg,
                    total_requests,
                    successful_requests,
                    failed_requests,
                    success_rate,
                    failure_rate,
                    avg_response_time,
                    min_response_time,
                    max_response_time,
                    p50_response_time,
                    p95_response_time,
                    p99_response_time
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    repo_id,
                    run_id,
                    data.get("target_url"),
                    data.get("config", {}).get("test_type"),
                    data.get("config", {}).get("duration"),
                    vus.get("max"),
                    vus.get("avg"),
                    req.get("total"),
                    req.get("successful"),
                    req.get("failed"),
                    req.get("success_rate"),
                    req.get("failed_rate"),
                    rt.get("avg"),
                    rt.get("min"),
                    rt.get("max"),
                    rt.get("p50"),
                    rt.get("p95"),
                    rt.get("p99"),
                ),
            )

        return True

    except Exception as e:
        print("Failed storing performance metrics:", e)
        return False



def fetch_performance_run(run_id: str):
    try:
        conn = _get_conn()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    repo_id,
                    run_id,
                    target_url,
                    test_type,
                    duration,
                    vus_max,
                    vus_avg,
                    total_requests,
                    successful_requests,
                    failed_requests,
                    success_rate,
                    failure_rate,
                    avg_response_time,
                    min_response_time,
                    max_response_time,
                    p50_response_time,
                    p95_response_time,
                    p99_response_time,
                    created_at
                FROM performance_runs
                WHERE run_id = %s
                LIMIT 1
                """,
                (run_id,)
            )

            row = cur.fetchone()

        if not row:
            return None

        return {
            "repo_id": row[0],
            "run_id": row[1],
            "target_url": row[2],
            "test_type": row[3],
            "duration": row[4],
            "vus_max": row[5],
            "vus_avg": row[6],
            "total_requests": row[7],
            "successful_requests": row[8],
            "failed_requests": row[9],
            "success_rate": row[10],
            "failure_rate": row[11],
            "avg_response_time": row[12],
            "min_response_time": row[13],
            "max_response_time": row[14],
            "p50_response_time": row[15],
            "p95_response_time": row[16],
            "p99_response_time": row[17],
            "created_at": row[18],
        }

    except Exception as e:
        print("Error fetching performance run:", e)
        return None
    

__all__ = [
    "init_snowflake",
    "store_simulation_run",
    "store_affected_files",
    "store_ai_insight",
    "fetch_latest_simulation_report",
    "fetch_simulation_report",
    "fetch_severity_summary",
    "store_performance_run",
    "fetch_performance_run",
]
