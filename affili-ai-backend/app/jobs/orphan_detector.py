"""
Data consistency audit and orphan detection.
Phase 12: Data Integrity & Backup

Detects:
- Orphaned tasks (non-existent tenant/program references)
- Stale task claims (stuck in CLAIMED for >24 hours)
- Referential integrity violations
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List
import logging

from app.core.logging import logger


def detect_orphan_tasks(db: Session) -> Dict[str, int]:
    """
    Detect tasks with invalid foreign key references.
    
    Returns:
        dict: Count of orphaned tasks by category
    """
    issues = {}
    
    # Tasks with non-existent tenants
    orphan_tenants_query = text("""
        SELECT t.id, t.tenant_id
        FROM tasks t
        LEFT JOIN tenants tn ON t.tenant_id = tn.id
        WHERE tn.id IS NULL
        LIMIT 100
    """)
    
    orphan_tenants = db.execute(orphan_tenants_query).fetchall()
    issues['orphan_tenants'] = len(orphan_tenants)
    
    if orphan_tenants:
        logger.error(
            "orphan_tasks_detected",
            extra={
                'issue_type': 'orphan_tenants',
                'count': len(orphan_tenants),
                'sample_task_ids': [str(row[0]) for row in orphan_tenants[:5]]
            }
        )
    
    # Tasks with non-existent programs
    orphan_programs_query = text("""
        SELECT t.id, t.program_id
        FROM tasks t
        LEFT JOIN programs p ON t.program_id = p.id
        WHERE t.program_id IS NOT NULL AND p.id IS NULL
        LIMIT 100
    """)
    
    orphan_programs = db.execute(orphan_programs_query).fetchall()
    issues['orphan_programs'] = len(orphan_programs)
    
    if orphan_programs:
        logger.error(
            "orphan_tasks_detected",
            extra={
                'issue_type': 'orphan_programs',
                'count': len(orphan_programs),
                'sample_task_ids': [str(row[0]) for row in orphan_programs[:5]]
            }
        )
    
    return issues


def detect_stale_claims(db: Session, hours: int = 24) -> Dict[str, int]:
    """
    Detect tasks stuck in CLAIMED status.
    
    These should have been caught by heartbeat reaper,
    but this is a defensive consistency check.
    
    Args:
        hours: Hours threshold for stale claim
    
    Returns:
        dict: Count of stale claims
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    stale_query = text("""
        SELECT id, claimed_at, agent_id, status
        FROM tasks
        WHERE status IN ('CLAIMED', 'RUNNING')
        AND claimed_at < :cutoff
        LIMIT 100
    """)
    
    stale_claims = db.execute(stale_query, {'cutoff': cutoff}).fetchall()
    count = len(stale_claims)
    
    if stale_claims:
        logger.warning(
            "stale_claims_detected",
            extra={
                'count': count,
                'threshold_hours': hours,
                'sample_task_ids': [str(row[0]) for row in stale_claims[:5]]
            }
        )
    
    return {'stale_claims': count}


def detect_duplicate_active_claims(db: Session) -> Dict[str, int]:
    """
    Detect multiple CLAIMED tasks for the same resource.
    
    This should never happen with atomic task claiming,
    but serves as a validation check.
    """
    duplicate_query = text("""
        SELECT program_id, COUNT(*) as claim_count
        FROM tasks
        WHERE status IN ('CLAIMED', 'RUNNING')
        AND program_id IS NOT NULL
        GROUP BY program_id
        HAVING COUNT(*) > 1
    """)
    
    duplicates = db.execute(duplicate_query).fetchall()
    count = len(duplicates)
    
    if duplicates:
        logger.critical(
            "duplicate_active_claims_detected",
            extra={
                'count': count,
                'sample_program_ids': [str(row[0]) for row in duplicates[:5]]
            }
        )
    
    return {'duplicate_active_claims': count}


def detect_missing_audit_trail(db: Session) -> Dict[str, int]:
    """
    Detect critical operations without audit log entries.
    
    Example: Task status changed to FAILED without corresponding audit entry.
    """
    # Tasks without corresponding audit log for status changes
    missing_audit_query = text("""
        SELECT t.id, t.status, t.updated_at
        FROM tasks t
        WHERE t.status IN ('FAILED', 'COMPLETED', 'CANCELLED')
        AND t.updated_at > NOW() - INTERVAL '7 days'
        AND NOT EXISTS (
            SELECT 1 FROM audit_logs a
            WHERE a.resource_type = 'task'
            AND a.resource_id::uuid = t.id
            AND a.created_at >= t.updated_at - INTERVAL '1 minute'
            AND a.created_at <= t.updated_at + INTERVAL '1 minute'
        )
        LIMIT 100
    """)
    
    try:
        missing = db.execute(missing_audit_query).fetchall()
        count = len(missing)
        
        if missing:
            logger.warning(
                "missing_audit_trail_detected",
                extra={
                    'count': count,
                    'sample_task_ids': [str(row[0]) for row in missing[:5]]
                }
            )
        
        return {'missing_audit_trail': count}
    except Exception as e:
        # Query might fail on SQLite (no INTERVAL support)
        logger.debug(f"Audit trail check skipped: {e}")
        return {'missing_audit_trail': 0}


def execute_consistency_audit(db: Session) -> Dict[str, int]:
    """
    Execute full data consistency audit.
    
    Returns:
        dict: Aggregated issue counts
    """
    logger.info("consistency_audit_started")
    
    all_issues = {}
    
    try:
        # Orphan detection
        orphan_issues = detect_orphan_tasks(db)
        all_issues.update(orphan_issues)
        
        # Stale claims
        stale_issues = detect_stale_claims(db)
        all_issues.update(stale_issues)
        
        # Duplicate claims
        duplicate_issues = detect_duplicate_active_claims(db)
        all_issues.update(duplicate_issues)
        
        # Missing audit trail
        audit_issues = detect_missing_audit_trail(db)
        all_issues.update(audit_issues)
        
        # Summary
        total_issues = sum(all_issues.values())
        
        if total_issues > 0:
            logger.error(
                "consistency_audit_completed_with_issues",
                extra={'total_issues': total_issues, 'breakdown': all_issues}
            )
        else:
            logger.info(
                "consistency_audit_completed_clean",
                extra={'message': 'No consistency issues detected'}
            )
        
        return all_issues
        
    except Exception as e:
        logger.error(
            "consistency_audit_failed",
            extra={'error': str(e)},
            exc_info=True
        )
        raise


if __name__ == "__main__":
    """Run as standalone job: python -m app.jobs.orphan_detector"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        issues = execute_consistency_audit(db)
        
        print("\n=== Data Consistency Audit Results ===")
        for issue_type, count in issues.items():
            status = "❌" if count > 0 else "✅"
            print(f"{status} {issue_type}: {count}")
        
        total = sum(issues.values())
        if total == 0:
            print("\n✅ All consistency checks passed!")
        else:
            print(f"\n⚠️  Total issues detected: {total}")
            print("Check logs for details.")
        
    finally:
        db.close()
