from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict
from app.models.schemas import Source, EvaluationResult


class AgentState(TypedDict):
    """State object shared between agents in the workflow"""
    
    # Input
    original_query: str
    session_id: Optional[str]
    
    # Query parsing
    parsed_query: Dict[str, Any]
    intent: str
    entities: List[str]
    query_type: str  # financial, technical, business, general
    
    # Retrieval
    retrieved_sources: List[Source]
    retrieval_successful: bool
    
    # Analysis
    analysis_result: str
    reasoning_steps: List[str]
    confidence_score: float
    
    # Summary
    final_answer: str
    key_points: List[str]
    citations: List[str]
    
    # Evaluation
    evaluation_result: Optional[EvaluationResult]
    
    # Execution metadata
    execution_time: float
    agent_steps: List[Dict[str, Any]]
    errors: List[str]