"""
Data retention cleanup job for GDPR compliance.
Phase 12: Data Integrity & Backup

Executes automated cleanup of:
- Old completed/failed tasks
- Expired audit logs
- Inactive user data (anonymization)
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.task import Task, TaskStatus
from app.models.audit_log import AuditLog
from app.models.user import User
from app.core.logging import logger


class RetentionPolicy:
    """Retention period configuration."""
    COMPLETED_TASKS_DAYS = 90
    FAILED_TASKS_DAYS = 30
    AUDIT_LOGS_DAYS = 730  # 2 years
    INACTIVE_USERS_DAYS = 365


def cleanup_old_tasks(db: Session, dry_run: bool = False) -> dict:
    """
    Delete old completed and failed tasks using BATCHED deletes.
    
    CRITICAL: Unbatched DELETE can lock table and spike I/O.
    Batching prevents long-running transactions and allows concurrent access.
    
    Args:
        db: Database session
        dry_run: If True, only count records without deleting
    
    Returns:
        dict: Cleanup statistics
    """
    import time
    from sqlalchemy import text
    
    now = datetime.utcnow()
    stats = {'completed_deleted': 0, 'failed_deleted': 0}
    BATCH_SIZE = 1000
    
    # Completed tasks (90 days) - BATCHED
    completed_cutoff = now - timedelta(days=RetentionPolicy.COMPLETED_TASKS_DAYS)
    
    if dry_run:
        count = db.execute(text("""
            SELECT COUNT(*) FROM tasks
            WHERE status IN ('COMPLETED', 'SUCCESS')
            AND completed_at < :cutoff
        """), {'cutoff': completed_cutoff}).scalar()
        stats['completed_tasks_count'] = count
    else:
        while True:
            # Delete in batches
            deleted = db.execute(text("""
                DELETE FROM tasks
                WHERE id IN (
                    SELECT id FROM tasks
                    WHERE status IN ('COMPLETED', 'SUCCESS')
                    AND completed_at < :cutoff
                    LIMIT :batch_size
                )
            """), {'cutoff': completed_cutoff, 'batch_size': BATCH_SIZE}).rowcount
            
            db.commit()
            stats['completed_deleted'] += deleted
            
            if deleted == 0:
                break
            
            logger.info(f"Deleted batch of {deleted} completed tasks")
            time.sleep(0.1)  # Rate limit to reduce I/O pressure
    
    # Failed tasks (30 days) - BATCHED
    failed_cutoff = now - timedelta(days=RetentionPolicy.FAILED_TASKS_DAYS)
    
    if dry_run:
        count = db.execute(text("""
            SELECT COUNT(*) FROM tasks
            WHERE status IN ('FAILED', 'CANCELLED')
            AND completed_at < :cutoff
        """), {'cutoff': failed_cutoff}).scalar()
        stats['failed_tasks_count'] = count
    else:
        while True:
            deleted = db.execute(text("""
                DELETE FROM tasks
                WHERE id IN (
                    SELECT id FROM tasks
                    WHERE status IN ('FAILED', 'CANCELLED')
                    AND completed_at < :cutoff
                    LIMIT :batch_size
                )
            """), {'cutoff': failed_cutoff, 'batch_size': BATCH_SIZE}).rowcount
            
            db.commit()
            stats['failed_deleted'] += deleted
            
            if deleted == 0:
                break
            
            logger.info(f"Deleted batch of {deleted} failed tasks")
            time.sleep(0.1)
    
    logger.info(
        "retention_cleanup_tasks_completed",
        extra={
            'completed_deleted': stats.get('completed_deleted', 0),
            'failed_deleted': stats.get('failed_deleted', 0),
            'retention_policy_days': f"completed:{RetentionPolicy.COMPLETED_TASKS_DAYS}, failed:{RetentionPolicy.FAILED_TASKS_DAYS}"
        }
    )
    
    return stats


def cleanup_old_audit_logs(db: Session, dry_run: bool = False) -> dict:
    """
    Delete audit logs older than 2 years.
    
    Compliance requirement: Retain security logs for regulatory audits.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=RetentionPolicy.AUDIT_LOGS_DAYS)
    
    query = db.query(AuditLog).filter(AuditLog.created_at < cutoff)
    count = query.count()
    
    if not dry_run:
        deleted = query.delete(synchronize_session=False)
        db.commit()
        
        logger.info(
            "retention_cleanup_audit_logs",
            extra={
                'deleted_count': deleted,
                'cutoff_date': cutoff.isoformat(),
                'retention_days': RetentionPolicy.AUDIT_LOGS_DAYS
            }
        )
    
    return {'audit_logs_count': count}


def anonymize_inactive_users(db: Session, dry_run: bool = False) -> dict:
    """
    Anonymize inactive user accounts for GDPR Article 17 (Right to Erasure).
    
    Strategy:
    - Keep user record for referential integrity
    - Anonymize email and remove password
    - Retain for audit trail
    """
    cutoff = datetime.utcnow() - timedelta(days=RetentionPolicy.INACTIVE_USERS_DAYS)
    
    inactive_users = db.query(User).filter(
        and_(
            User.is_active == False,
            User.created_at < cutoff,
            ~User.email.like('deleted_%@anonymized.local')  # Not already anonymized
        )
    ).all()
    
    count = len(inactive_users)
    
    if not dry_run:
        for user in inactive_users:
            user.email = f"deleted_{user.id}@anonymized.local"
            user.hashed_password = None
            
        db.commit()
        
        logger.info(
            "retention_anonymize_users",
            extra={
                'anonymized_count': count,
                'cutoff_date': cutoff.isoformat(),
                'retention_days': RetentionPolicy.INACTIVE_USERS_DAYS
            }
        )
    
    return {'inactive_users_count': count}


def execute_retention_cleanup(db: Session, dry_run: bool = False) -> dict:
    """
    Execute full retention policy cleanup.
    
    Args:
        dry_run: If True, simulate cleanup without making changes
    
    Returns:
        dict: Aggregated cleanup statistics
    """
    logger.info(
        "retention_cleanup_started",
        extra={'dry_run': dry_run}
    )
    
    stats = {}
    
    try:
        # Cleanup tasks
        task_stats = cleanup_old_tasks(db, dry_run)
        stats.update(task_stats)
        
        # Cleanup audit logs
        audit_stats = cleanup_old_audit_logs(db, dry_run)
        stats.update(audit_stats)
        
        # Anonymize users
        user_stats = anonymize_inactive_users(db, dry_run)
        stats.update(user_stats)
        
        logger.info(
            "retention_cleanup_completed",
            extra={'stats': stats, 'dry_run': dry_run}
        )
        
        return stats
        
    except Exception as e:
        logger.error(
            "retention_cleanup_failed",
            extra={'error': str(e)},
            exc_info=True
        )
        db.rollback()
        raise


if __name__ == "__main__":
    """Run as standalone job: python -m app.jobs.data_retention"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # First run in dry-run mode
        print("=== DRY RUN ===")
        dry_stats = execute_retention_cleanup(db, dry_run=True)
        print(f"Would delete: {dry_stats}")
        
        # Uncomment to execute actual cleanup
        # print("\n=== ACTUAL CLEANUP ===")
        # actual_stats = execute_retention_cleanup(db, dry_run=False)
        # print(f"Deleted: {actual_stats}")
        
    finally:
        db.close()
