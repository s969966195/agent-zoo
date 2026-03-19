"""SQLAlchemy database models for Zoo Multi-Agent System."""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from core.config import get_config

Base = declarative_base()


class AnimalMessageModel(Base):
    """Database model for AnimalMessage."""
    __tablename__ = "animal_messages"

    id = Column(String(36), primary_key=True)
    type = Column(String(50), default="message")
    animal_id = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    thread_id = Column(String(36), ForeignKey("threads.id"), nullable=False)
    mentions = Column(JSON, default=list)
    role = Column(String(50), default="user")
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default=dict)

    # Relationships
    thread = relationship("ThreadModel", back_populates="messages")


class SessionModel(Base):
    """Database model for Session."""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON, default=dict)

    # Relationships
    messages = relationship("AnimalMessageModel", back_populates="thread")
    animal_sessions = relationship("AnimalSessionModel", back_populates="session")


class AnimalSessionModel(Base):
    """Database model for AnimalSession."""
    __tablename__ = "animal_sessions"

    id = Column(String(36), primary_key=True)
    animal_id = Column(String(50), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    context = Column(JSON, default=dict)

    # Relationships
    session = relationship("SessionModel", back_populates="animal_sessions")


class InvocationRecordModel(Base):
    """Database model for InvocationRecord."""
    __tablename__ = "invocation_records"

    id = Column(String(36), primary_key=True)
    caller_animal = Column(String(50), nullable=False)
    target_animal = Column(String(50), nullable=False)
    callback_token = Column(String(255), nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50), default="pending")
    request_data = Column(JSON, default=dict)
    response_data = Column(JSON)


class ThreadModel(Base):
    """Database model for Thread."""
    __tablename__ = "threads"

    id = Column(String(36), primary_key=True)
    title = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime)
    participant_animals = Column(JSON, default=list)
    extra_data = Column(JSON, default=dict)

    # Relationships
    messages = relationship("AnimalMessageModel", back_populates="thread")


class RedisFallbackData(Base):
    """Fallback storage for Redis data (SQLite)."""
    __tablename__ = "redis_fallback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Database:
    """Database manager using SQLAlchemy with async support."""

    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.session_factory = None

    async def connect(self) -> None:
        """Initialize database connection."""
        from sqlalchemy.ext.asyncio import create_async_engine

        self.engine = create_async_engine(
            self.config.database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self) -> None:
        """Close database connection."""
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()

    async def save_message(self, session: AsyncSession, message: dict) -> AnimalMessageModel:
        """Save a message to the database."""
        db_message = AnimalMessageModel(**message)
        session.add(db_message)
        await session.commit()
        await session.refresh(db_message)
        return db_message

    async def save_thread(self, session: AsyncSession, thread: dict) -> ThreadModel:
        """Save a thread to the database."""
        db_thread = ThreadModel(**thread)
        session.add(db_thread)
        await session.commit()
        await session.refresh(db_thread)
        return db_thread

    async def save_session(self, session: AsyncSession, session_data: dict) -> SessionModel:
        """Save a session to the database."""
        db_session = SessionModel(**session_data)
        session.add(db_session)
        await session.commit()
        await session.refresh(db_session)
        return db_session

    async def save_invocation(self, session: AsyncSession, invocation: dict) -> InvocationRecordModel:
        """Save an invocation record to the database."""
        db_invocation = InvocationRecordModel(**invocation)
        session.add(db_invocation)
        await session.commit()
        await session.refresh(db_invocation)
        return db_invocation

    async def get_session_by_id(self, session: AsyncSession, session_id: str) -> Optional[SessionModel]:
        """Get a session by ID."""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_thread_by_id(self, session: AsyncSession, thread_id: str) -> Optional[ThreadModel]:
        """Get a thread by ID."""
        stmt = select(ThreadModel).where(ThreadModel.id == thread_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_messages_by_thread(
        self,
        session: AsyncSession,
        thread_id: str,
        limit: int = 100
    ) -> List[AnimalMessageModel]:
        """Get messages for a thread."""
        stmt = (
            select(AnimalMessageModel)
            .where(AnimalMessageModel.thread_id == thread_id)
            .order_by(AnimalMessageModel.timestamp.asc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def update_session(self, session: AsyncSession, session_id: str, updates: dict) -> Optional[SessionModel]:
        """Update a session."""
        db_session = await self.get_session_by_id(session, session_id)
        if db_session:
            for key, value in updates.items():
                setattr(db_session, key, value)
            await session.commit()
            await session.refresh(db_session)
        return db_session

    async def update_thread(self, session: AsyncSession, thread_id: str, updates: dict) -> Optional[ThreadModel]:
        """Update a thread."""
        db_thread = await self.get_thread_by_id(session, thread_id)
        if db_thread:
            for key, value in updates.items():
                setattr(db_thread, key, value)
            await session.commit()
            await session.refresh(db_thread)
        return db_thread

    async def get_all_sessions(self, session: AsyncSession) -> List[SessionModel]:
        """Get all sessions."""
        stmt = select(SessionModel).order_by(SessionModel.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_threads(self, session: AsyncSession) -> List[ThreadModel]:
        """Get all threads."""
        stmt = select(ThreadModel).order_by(ThreadModel.created_at.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())


# Global database instance
_database: Optional[Database] = None


async def get_database() -> Database:
    """Get or create the global database instance."""
    global _database
    if _database is None:
        _database = Database()
        await _database.connect()
    return _database


async def reset_database() -> None:
    """Reset the global database (for testing)."""
    global _database
    if _database:
        await _database.disconnect()
    _database = None
