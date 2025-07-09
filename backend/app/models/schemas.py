from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class Source(BaseModel):
    content: str
    filename: str
    page: Optional[int] = None
    relevance_score: float


class EvaluationResult(BaseModel):
    score: float
    rationale: str
    criteria: Dict[str, float]


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Source]
    evaluation: EvaluationResult
    session_id: str
    timestamp: datetime


class UploadRequest(BaseModel):
    filename: str
    content_type: str


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    document_id: str


class QueryHistoryResponse(BaseModel):
    queries: List[QueryResponse]
    total_count: int
    page: int
    page_size: int


class EvaluationRequest(BaseModel):
    query_id: str
    
    
class AgentStep(BaseModel):
    step_name: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time: float
    status: str


class AgentTrace(BaseModel):
    trace_id: str
    query: str
    steps: List[AgentStep]
    total_execution_time: float
    final_output: Dict[str, Any]