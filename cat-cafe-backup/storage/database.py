"""
Cat Café Multi-Agent System - Database ORM with SQLAlchemy

Persistent storage layer for sessions, messages, and invocations.
"""

import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    Text,
    ForeignKey,
    JSON,
    Boolean,
    Integer,
    Index,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    scoped_session,
)
from sqlalchemy.dialects.postgresql import JSONB

from core.models import Session as SessionModel, AgentMessage, InvocationRecord

# Base class for models
Base = declarative_base()

# Database configuration
DATABASE_URL = "sqlite:///./cat-cafe.db"

# SQLite-specific JSON handling
if "sqlite" in DATABASE_URL:
    JSON_TYPE = JSON
else:
    JSON_TYPE = JSONB


class SessionDB(Base):
    """Persistent Session model."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    agent_sessions = Column(JSON_TYPE, default=dict)
    
    # Relationship to messages
    messages = relationship(
        "MessageDB",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    
    def to_model(self) -> SessionModel:
        """Convert to domain model."""
        return SessionModel(
            id=self.id,
            created_at=self.created_at,
            last_active=self.last_active,
            messages=[m.to_model() for m in self.messages],
            agent_sessions=self.agent_sessions or {},
        )
    
    @classmethod
    def from_model(cls, model: SessionModel) -> "SessionDB":
        """Create from domain model."""
        return cls(
            id=model.id,
            created_at=model.created_at,
            last_active=model.last_active,
            agent_sessions=model.agent_sessions,
        )


class MessageDB(Base):
    """Persistent Message model."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    type = Column(String(50), nullable=False, index=True)
    agent_id = Column(String(50), nullable=True)
    content = Column(Text, nullable=True)
    thread_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    mentions = Column(JSON_TYPE, default=list)
    metadata_json = Column("metadata", JSON_TYPE, default=dict)
    
    # Foreign key to session
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"))
    session = relationship("SessionDB", back_populates="messages")
    
    def to_model(self) -> AgentMessage:
        """Convert to domain model."""
        return AgentMessage(
            id=self.id,
            type=self.type,
            agent_id=self.agent_id,
            content=self.content,
            thread_id=self.thread_id,
            timestamp=self.timestamp,
            mentions=self.mentions or [],
            metadata=self.metadata_json or {},
        )
    
    @classmethod
    def from_model(cls, model: AgentMessage, session_id: Optional[str] = None) -> "MessageDB":
        """Create from domain model."""
        return cls(
            id=model.id,
            type=model.type,
            agent_id=model.agent_id,
            content=model.content,
            thread_id=model.thread_id,
            timestamp=model.timestamp,
            mentions=model.mentions,
            metadata_json=model.metadata,
            session_id=session_id,
        )


class InvocationRecordDB(Base):
    """Persistent InvocationRecord model."""
    __tablename__ = "invocation_records"
    
    id = Column(String(36), primary_key=True)
    caller_agent = Column(String(50), nullable=True)
    target_agent = Column(String(50), nullable=False, index=True)
    thread_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    callback_token = Column(String(36), nullable=False)
    status = Column(String(20), default="pending", index=True)
    
    def to_model(self) -> InvocationRecord:
        """Convert to domain model."""
        return InvocationRecord(
            id=self.id,
            caller_agent=self.caller_agent,
            target_agent=self.target_agent,
            thread_id=self.thread_id,
            timestamp=self.timestamp,
            callback_token=self.callback_token,
            status=self.status,
        )
    
    @classmethod
    def from_model(cls, model: InvocationRecord) -> "InvocationRecordDB":
        """Create from domain model."""
        return cls(
            id=model.id,
            caller_agent=model.caller_agent,
            target_agent=model.target_agent,
            thread_id=model.thread_id,
            timestamp=model.timestamp,
            callback_token=model.callback_token,
            status=model.status,
        )


class DatabaseEngine:
    """
    SQLAlchemy database engine wrapper for persistent storage.
    
    Supports both SQLite (for development) and PostgreSQL (for production).
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def _initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._initialized:
            return
        
        # Create engine
        if "sqlite" in self.database_url:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},
                pool_size=5,
                max_overflow=10,
            )
        else:
            self.engine = create_engine(
                self.database_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
        self._initialized = True
    
    def get_session(self):
        """Get a new database session."""
        if not self._initialized:
            self._initialize()
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """Context manager for database sessions with automatic commit/rollback."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_sessions(self) -> List[SessionModel]:
        """Get all sessions from database."""
        with self.session_scope() as session:
            db_sessions = session.query(SessionDB).all()
            return [s.to_model() for s in db_sessions]
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID."""
        with self.session_scope() as session:
            db_session = session.query(SessionDB).filter(SessionDB.id == session_id).first()
            if db_session:
                return db_session.to_model()
            return None
    
    def get_session_by_thread(self, thread_id: str) -> Optional[SessionModel]:
        """Get session by thread ID."""
        with self.session_scope() as session:
            db_session = session.query(SessionDB).filter(
                SessionDB.messages.any(thread_id=thread_id)
            ).first()
            if db_session:
                return db_session.to_model()
            return None
    
    def save_session(self, session: SessionModel) -> SessionModel:
        """Save or update a session."""
        with self.session_scope() as session_db:
            db_session = session_db.query(SessionDB).filter(SessionDB.id == session.id).first()
            
            if db_session is None:
                db_session = SessionDB.from_model(session)
                session_db.add(db_session)
            else:
                db_session.last_active = session.last_active
                db_session.agent_sessions = session.agent_sessions
            
            # Save messages
            for message in session.messages:
                db_message = session_db.query(MessageDB).filter(MessageDB.id == message.id).first()
                if db_message is None:
                    db_message = MessageDB.from_model(message, session_id=session.id)
                    session_db.add(db_message)
            
            session_db.flush()
            session_db.refresh(db_session)
            
            return db_session.to_model()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        with self.session_scope() as session_db:
            result = session_db.query(SessionDB).filter(SessionDB.id == session_id).delete()
            return result > 0
    
    def get_invocation_records(
        self,
        status: Optional[str] = None,
        thread_id: Optional[str] = None,
        target_agent: Optional[str] = None,
    ) -> List[InvocationRecord]:
        """Get invocation records with optional filters."""
        with self.session_scope() as session_db:
            query = session_db.query(InvocationRecordDB)
            
            if status:
                query = query.filter(InvocationRecordDB.status == status)
            
            if thread_id:
                query = query.filter(InvocationRecordDB.thread_id == thread_id)
            
            if target_agent:
                query = query.filter(InvocationRecordDB.target_agent == target_agent)
            
            return [r.to_model() for r in query.all()]
    
    def save_invocation_record(self, record: InvocationRecord) -> InvocationRecord:
        """Save or update an invocation record."""
        with self.session_scope() as session_db:
            db_record = session_db.query(InvocationRecordDB).filter(
                InvocationRecordDB.id == record.id
            ).first()
            
            if db_record is None:
                db_record = InvocationRecordDB.from_model(record)
                session_db.add(db_record)
            else:
                db_record.status = record.status
                db_record.target_agent = record.target_agent
            
            session_db.flush()
            session_db.refresh(db_record)
            
            return db_record.to_model()
    
    def close(self) -> None:
        """Close the database engine."""
        if self.engine:
            self.engine.dispose()


# Global instance
db_engine = DatabaseEngine()


def get_db() -> DatabaseEngine:
    """Get the database engine instance."""
    return db_engine


@contextmanager
def database_session():
    """Context manager for database operations."""
    try:
        yield db_engine
    finally:
        pass


__all__ = [
    "Base",
    "SessionDB",
    "MessageDB",
    "InvocationRecordDB",
    "DatabaseEngine",
    "db_engine",
    "get_db",
    "database_session",
]
