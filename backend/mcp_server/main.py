#!/usr/bin/env python3
"""
InsightBot MCP Server
Model Context Protocol server providing tools for document querying and management.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from app.agents.workflow import workflow
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store
from app.models.database import SessionLocal, Query as QueryModel
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = Server("insightbot-mcp")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools for the MCP server."""
    tools = [
        Tool(
            name="query_documents",
            description="Query documents using AI-powered analysis with LangGraph workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or query to search for in documents"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for tracking related queries"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="upload_document",
            description="Upload and process a document for future querying",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The document content to process"
                    },
                    "filename": {
                        "type": "string",
                        "description": "Name of the document file"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "MIME type of the document",
                        "enum": ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
                    }
                },
                "required": ["content", "filename", "content_type"]
            }
        ),
        Tool(
            name="get_document_stats",
            description="Get statistics about the document collection",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_similar_documents",
            description="Find documents similar to a given query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to find similar documents"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum similarity threshold",
                        "default": 0.7
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_query_history",
            description="Retrieve query history with evaluation scores",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID to filter queries"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of queries to return",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="evaluate_response",
            description="Evaluate the quality of a query response",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The original query"
                    },
                    "answer": {
                        "type": "string",
                        "description": "The response to evaluate"
                    },
                    "sources": {
                        "type": "array",
                        "description": "Source documents used in the response",
                        "items": {
                            "type": "object",
                            "properties": {
                                "content": {"type": "string"},
                                "filename": {"type": "string"},
                                "relevance_score": {"type": "number"}
                            }
                        }
                    }
                },
                "required": ["query", "answer"]
            }
        )
    ]
    return ListToolsResult(tools=tools)

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls from the MCP client."""
    
    try:
        if name == "query_documents":
            return await handle_query_documents(arguments)
        elif name == "upload_document":
            return await handle_upload_document(arguments)
        elif name == "get_document_stats":
            return await handle_get_document_stats(arguments)
        elif name == "search_similar_documents":
            return await handle_search_similar_documents(arguments)
        elif name == "get_query_history":
            return await handle_get_query_history(arguments)
        elif name == "evaluate_response":
            return await handle_evaluate_response(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )
            ]
        )

async def handle_query_documents(args: Dict[str, Any]) -> CallToolResult:
    """Handle document querying using the LangGraph workflow."""
    query = args["query"]
    session_id = args.get("session_id")
    
    # Run the workflow
    result = workflow.run(query, session_id)
    
    # Format response
    response_text = f"**Query:** {query}\n\n"
    response_text += f"**Answer:** {result.get('final_answer', 'No answer generated')}\n\n"
    
    # Add sources if available
    sources = result.get("retrieved_sources", [])
    if sources:
        response_text += "**Sources:**\n"
        for i, source in enumerate(sources, 1):
            response_text += f"{i}. {source.filename} (relevance: {source.relevance_score:.2f})\n"
            response_text += f"   {source.content[:200]}...\n\n"
    
    # Add evaluation if available
    evaluation = result.get("evaluation_result")
    if evaluation:
        response_text += f"**Evaluation Score:** {evaluation.score:.1f}/5.0\n"
        response_text += f"**Rationale:** {evaluation.rationale}\n\n"
    
    # Add execution metadata
    response_text += f"**Execution Time:** {result.get('execution_time', 0):.2f}s\n"
    response_text += f"**Session ID:** {result.get('session_id', 'N/A')}\n"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_text
            )
        ]
    )

async def handle_upload_document(args: Dict[str, Any]) -> CallToolResult:
    """Handle document upload and processing."""
    content = args["content"]
    filename = args["filename"]
    content_type = args["content_type"]
    
    # Create temporary file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f"_{filename}", delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        # Process document
        document_id = document_processor.process_document(
            file_path=tmp_file_path,
            filename=filename,
            content_type=content_type
        )
        
        # Get stats
        doc_count = vector_store.get_document_count()
        chunk_count = vector_store.get_chunk_count()
        
        response_text = f"**Document Processed Successfully**\n\n"
        response_text += f"**Filename:** {filename}\n"
        response_text += f"**Document ID:** {document_id}\n"
        response_text += f"**Content Type:** {content_type}\n"
        response_text += f"**Total Documents:** {doc_count}\n"
        response_text += f"**Total Chunks:** {chunk_count}\n"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text
                )
            ]
        )
        
    finally:
        # Clean up temporary file
        os.unlink(tmp_file_path)

async def handle_get_document_stats(args: Dict[str, Any]) -> CallToolResult:
    """Get document collection statistics."""
    doc_count = vector_store.get_document_count()
    chunk_count = vector_store.get_chunk_count()
    
    # Get query statistics from database
    db = SessionLocal()
    try:
        total_queries = db.query(QueryModel).count()
        avg_score = db.query(QueryModel).filter(
            QueryModel.evaluation_score.isnot(None)
        ).with_entities(QueryModel.evaluation_score).all()
        
        avg_evaluation_score = sum(score[0] for score in avg_score) / len(avg_score) if avg_score else 0.0
        
    finally:
        db.close()
    
    response_text = f"**Document Collection Statistics**\n\n"
    response_text += f"**Total Documents:** {doc_count}\n"
    response_text += f"**Total Chunks:** {chunk_count}\n"
    response_text += f"**Total Queries:** {total_queries}\n"
    response_text += f"**Average Evaluation Score:** {avg_evaluation_score:.2f}/5.0\n"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_text
            )
        ]
    )

async def handle_search_similar_documents(args: Dict[str, Any]) -> CallToolResult:
    """Search for similar documents."""
    query = args["query"]
    limit = args.get("limit", 5)
    threshold = args.get("threshold", 0.7)
    
    # Search for similar documents
    sources = vector_store.search(query, k=limit, score_threshold=threshold)
    
    if not sources:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"No documents found matching '{query}' with threshold {threshold}"
                )
            ]
        )
    
    response_text = f"**Similar Documents for:** {query}\n\n"
    
    for i, source in enumerate(sources, 1):
        response_text += f"**{i}. {source.filename}** (Score: {source.relevance_score:.3f})\n"
        response_text += f"{source.content[:300]}...\n\n"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_text
            )
        ]
    )

async def handle_get_query_history(args: Dict[str, Any]) -> CallToolResult:
    """Get query history."""
    session_id = args.get("session_id")
    limit = args.get("limit", 10)
    
    db = SessionLocal()
    try:
        query = db.query(QueryModel)
        
        if session_id:
            query = query.filter(QueryModel.session_id == session_id)
        
        queries = query.order_by(QueryModel.timestamp.desc()).limit(limit).all()
        
        if not queries:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="No query history found"
                    )
                ]
            )
        
        response_text = f"**Query History** (Last {len(queries)} queries)\n\n"
        
        for i, query_record in enumerate(queries, 1):
            response_text += f"**{i}. {query_record.query_text}**\n"
            response_text += f"   Score: {query_record.evaluation_score or 'N/A'}\n"
            response_text += f"   Time: {query_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            response_text += f"   Session: {query_record.session_id or 'N/A'}\n\n"
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=response_text
                )
            ]
        )
        
    finally:
        db.close()

async def handle_evaluate_response(args: Dict[str, Any]) -> CallToolResult:
    """Evaluate a query response."""
    from app.agents.evaluator import EvaluatorAgent
    
    query = args["query"]
    answer = args["answer"]
    sources = args.get("sources", [])
    
    # Create evaluator and evaluate
    evaluator = EvaluatorAgent()
    evaluation = evaluator.evaluate_standalone(query, answer, sources)
    
    response_text = f"**Response Evaluation**\n\n"
    response_text += f"**Query:** {query}\n\n"
    response_text += f"**Overall Score:** {evaluation.score:.1f}/5.0\n\n"
    response_text += f"**Rationale:** {evaluation.rationale}\n\n"
    
    if evaluation.criteria:
        response_text += "**Detailed Scores:**\n"
        for criterion, score in evaluation.criteria.items():
            response_text += f"- {criterion.title()}: {score:.1f}/5.0\n"
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=response_text
            )
        ]
    )

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting InsightBot MCP Server...")
    
    # Initialize the server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="insightbot-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())