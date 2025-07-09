from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    JSON,
    Boolean,
    ForeignKey,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import settings

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    embedding_count = Column(Integer, default=0)
    
    # Relationships
    queries = relationship("Query", back_populates="document")


class Query(Base):
    __tablename__ = "queries"
    
    id = Column(String, primary_key=True)
    query_text = Column(Text, nullable=False)
    session_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Response data
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=False)  # List of source objects
    
    # Evaluation data
    evaluation_score = Column(Float, nullable=True)
    evaluation_rationale = Column(Text, nullable=True)
    evaluation_criteria = Column(JSON, nullable=True)
    
    # Agent execution data
    execution_time = Column(Float, nullable=True)
    agent_steps = Column(JSON, nullable=True)
    
    # Foreign keys
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="queries")


class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True)
    query_id = Column(String, ForeignKey("queries.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    execution_time = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # success, error, timeout
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    metadata = Column(JSON, nullable=True)


# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()