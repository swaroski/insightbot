import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from loguru import logger

from app.config import settings
from app.models.database import create_tables, get_db, Query as QueryModel, Document as DocumentModel
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
    QueryHistoryResponse,
    EvaluationRequest,
    EvaluationResult,
    AgentTrace
)
from app.agents.workflow import workflow
from app.agents.evaluator import EvaluatorAgent
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store

# Create FastAPI app
app = FastAPI(
    title="InsightBot API",
    description="AI-powered query and analysis platform with agent orchestration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("Database tables created")
    
    # Ensure upload directory exists
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory created: {settings.upload_dir}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "InsightBot API",
        "version": "1.0.0",
        "status": "active",
        "documents_count": vector_store.get_document_count(),
        "chunks_count": vector_store.get_chunk_count()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "vector_store_status": "active" if vector_store.index is not None else "inactive",
        "workflow_status": workflow.get_workflow_status()
    }


@app.post("/api/query", response_model=QueryResponse)
async def query_endpoint(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Main query endpoint that runs the agent workflow"""
    try:
        # Run the agent workflow
        result = workflow.run(request.query, request.session_id)
        
        # Create response
        response = QueryResponse(
            query=request.query,
            answer=result.get("final_answer", "No answer generated"),
            sources=result.get("retrieved_sources", []),
            evaluation=result.get("evaluation_result", EvaluationResult(
                score=0.0,
                rationale="No evaluation performed",
                criteria={}
            )),
            session_id=result.get("session_id", str(uuid.uuid4())),
            timestamp=datetime.utcnow()
        )
        
        # Save to database
        query_record = QueryModel(
            id=str(uuid.uuid4()),
            query_text=request.query,
            session_id=response.session_id,
            answer=response.answer,
            sources=[source.dict() for source in response.sources],
            evaluation_score=response.evaluation.score,
            evaluation_rationale=response.evaluation.rationale,
            evaluation_criteria=response.evaluation.criteria,
            execution_time=result.get("execution_time", 0.0),
            agent_steps=result.get("agent_steps", [])
        )
        
        db.add(query_record)
        db.commit()
        
        logger.info(f"Query processed successfully: {request.query[:50]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a document"""
    try:
        # Validate file type
        if not document_processor.is_supported_format(file.content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}"
            )
        
        # Validate file size
        if file.size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum: {settings.max_file_size} bytes"
            )
        
        # Save uploaded file
        file_path = os.path.join(settings.upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process document
        document_id = document_processor.process_document(
            file_path=file_path,
            filename=file.filename,
            content_type=file.content_type
        )
        
        # Clean up temporary file
        os.remove(file_path)
        
        response = UploadResponse(
            filename=file.filename,
            status="processed",
            message="Document uploaded and processed successfully",
            document_id=document_id
        )
        
        logger.info(f"Document uploaded successfully: {file.filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        
        # Clean up file if it exists
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )


@app.get("/api/queries", response_model=QueryHistoryResponse)
async def get_query_history(
    page: int = 1,
    page_size: int = 10,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get query history with pagination"""
    try:
        # Build query
        query = db.query(QueryModel)
        
        if session_id:
            query = query.filter(QueryModel.session_id == session_id)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        queries = query.offset(offset).limit(page_size).all()
        
        # Convert to response format
        query_responses = []
        for query_record in queries:
            query_response = QueryResponse(
                query=query_record.query_text,
                answer=query_record.answer,
                sources=[
                    {
                        "content": source["content"],
                        "filename": source["filename"],
                        "page": source.get("page"),
                        "relevance_score": source["relevance_score"]
                    } for source in query_record.sources
                ],
                evaluation=EvaluationResult(
                    score=query_record.evaluation_score or 0.0,
                    rationale=query_record.evaluation_rationale or "",
                    criteria=query_record.evaluation_criteria or {}
                ),
                session_id=query_record.session_id,
                timestamp=query_record.timestamp
            )
            query_responses.append(query_response)
        
        response = QueryHistoryResponse(
            queries=query_responses,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving query history: {str(e)}"
        )


@app.post("/api/eval", response_model=EvaluationResult)
async def re_evaluate_query(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """Re-evaluate a specific query result"""
    try:
        # Get query from database
        query_record = db.query(QueryModel).filter(QueryModel.id == request.query_id).first()
        
        if not query_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Query not found"
            )
        
        # Convert sources back to Source objects
        sources = [
            {
                "content": source["content"],
                "filename": source["filename"],
                "page": source.get("page"),
                "relevance_score": source["relevance_score"]
            } for source in query_record.sources
        ]
        
        # Re-evaluate using the evaluator agent
        evaluator = EvaluatorAgent()
        evaluation_result = evaluator.evaluate_standalone(
            query=query_record.query_text,
            answer=query_record.answer,
            sources=sources
        )
        
        # Update database record
        query_record.evaluation_score = evaluation_result.score
        query_record.evaluation_rationale = evaluation_result.rationale
        query_record.evaluation_criteria = evaluation_result.criteria
        db.commit()
        
        logger.info(f"Re-evaluated query {request.query_id} with score: {evaluation_result.score}")
        return evaluation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-evaluating query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error re-evaluating query: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics"""
    try:
        # Query statistics
        total_queries = db.query(QueryModel).count()
        avg_evaluation_score = db.query(QueryModel).filter(
            QueryModel.evaluation_score.isnot(None)
        ).with_entities(QueryModel.evaluation_score).all()
        
        avg_score = sum(score[0] for score in avg_evaluation_score) / len(avg_evaluation_score) if avg_evaluation_score else 0.0
        
        # Document statistics
        total_documents = db.query(DocumentModel).count()
        processed_documents = db.query(DocumentModel).filter(DocumentModel.processed == True).count()
        
        return {
            "queries": {
                "total": total_queries,
                "average_evaluation_score": round(avg_score, 2)
            },
            "documents": {
                "total": total_documents,
                "processed": processed_documents,
                "total_chunks": vector_store.get_chunk_count()
            },
            "vector_store": {
                "documents": vector_store.get_document_count(),
                "chunks": vector_store.get_chunk_count()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving statistics: {str(e)}"
        )


@app.get("/api/workflow/status")
async def get_workflow_status():
    """Get workflow status"""
    try:
        return workflow.get_workflow_status()
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow status: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)