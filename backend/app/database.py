"""
Contractor Vault - Database Module
SQLAlchemy setup with async support for SQLite MVP
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_engine():
    """
    Create SQLAlchemy engine.
    Uses StaticPool for SQLite to handle multi-threading.
    """
    settings = get_settings()
    
    connect_args = {}
    poolclass = None
    
    # SQLite-specific configuration
    if settings.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool
        
        engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            poolclass=poolclass,
            echo=settings.debug,
        )
        
        # Enable foreign key support for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL or other databases
        engine = create_engine(
            settings.database_url,
            echo=settings.debug,
        )
    
    return engine


# Create engine and session factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency that provides database session.
    SOC2 Requirement: Proper session cleanup to prevent connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Should be called on application startup.
    """
    # Import all models to register them with Base
    from app.models import credential, session_token, audit_log
    from app.models.user import User, OTPCode
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Manual migration: Add password_hash column to users table if it doesn't exist (for PostgreSQL)
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            # Check if column exists (PostgreSQL)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password_hash'
            """))
            if result.fetchone() is None:
                logger.info("Adding password_hash column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
                conn.commit()
                logger.info("password_hash column added successfully.")
    except Exception as e:
        logger.warning(f"Migration check skipped (might be SQLite): {e}")
    
    logger.info("Database tables created successfully.")
