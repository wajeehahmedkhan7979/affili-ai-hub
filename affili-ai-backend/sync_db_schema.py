from app.db.session import get_engine_instance
from app.db.base import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_db():
    engine = get_engine_instance()
    logger.info("Creating any missing tables...")
    try:
        # This will only create tables that don't exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema synchronization complete.")
    except Exception as e:
        logger.error(f"Error during schema synchronization: {e}")
        raise

if __name__ == "__main__":
    sync_db()
