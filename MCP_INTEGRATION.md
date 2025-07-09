# MCP Server Integration Guide

This guide explains how to use the InsightBot MCP (Model Context Protocol) server to integrate with AI assistants and other applications.

## Overview

The InsightBot MCP server provides a standardized way to access InsightBot's document querying and management capabilities from AI assistants like Claude Code, or other MCP-compatible applications.

## Features

### Available Tools

1. **query_documents** - Query documents using AI-powered analysis
2. **upload_document** - Upload and process documents
3. **get_document_stats** - Get document collection statistics
4. **search_similar_documents** - Find similar documents
5. **get_query_history** - Retrieve query history
6. **evaluate_response** - Evaluate response quality

## Setup

### 1. Docker Setup (Recommended)

```bash
# Start the full InsightBot stack including MCP server
docker-compose up -d

# MCP server will be available on port 3001
```

### 2. Local Development Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Start the MCP server
python -m mcp_server.main
```

### 3. Configure Environment Variables

```bash
export OPENAI_API_KEY="your-api-key"
export DATABASE_URL="sqlite:///./insightbot.db"
export FAISS_INDEX_PATH="./faiss_index"
export UPLOAD_DIR="./uploads"
```

## Usage Examples

### Basic Python Client

```python
import asyncio
import json
import subprocess

async def query_documents():
    # Start MCP server
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "mcp_server.main",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE
    )
    
    # Send query request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "query_documents",
            "arguments": {
                "query": "What is machine learning?",
                "session_id": "my-session"
            }
        }
    }
    
    # Send and receive
    message = json.dumps(request) + "\n"
    process.stdin.write(message.encode())
    await process.stdin.drain()
    
    response = await process.stdout.readline()
    result = json.loads(response.decode())
    
    return result
```

### Claude Code Integration

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "insightbot": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "cwd": "/path/to/insightbot/backend",
      "env": {
        "OPENAI_API_KEY": "your-api-key",
        "DATABASE_URL": "sqlite:///./insightbot.db",
        "FAISS_INDEX_PATH": "./faiss_index",
        "UPLOAD_DIR": "./uploads"
      }
    }
  }
}
```

### Docker MCP Server

```bash
# Build MCP server image
docker build -f docker/Dockerfile.mcp -t insightbot-mcp .

# Run standalone MCP server
docker run -p 3001:3001 \
  -e OPENAI_API_KEY="your-api-key" \
  -e DATABASE_URL="sqlite:///./insightbot.db" \
  -v $(pwd)/data:/app/data \
  insightbot-mcp
```

## Tool Reference

### 1. query_documents

Query documents using the full LangGraph workflow.

**Parameters:**
- `query` (string, required): The question to ask
- `session_id` (string, optional): Session identifier

**Example:**
```python
await client.call_tool("query_documents", {
    "query": "Compare Tesla and NVIDIA performance",
    "session_id": "analysis-session"
})
```

**Response:**
```
**Query:** Compare Tesla and NVIDIA performance

**Answer:** Based on the available documents, here's a comparison...

**Sources:**
1. financial_report.pdf (relevance: 0.95)
   Tesla reported revenue of $24.3 billion in Q3 2023...

**Evaluation Score:** 4.2/5.0
**Rationale:** Well-structured answer with good sources

**Execution Time:** 3.45s
**Session ID:** analysis-session
```

### 2. upload_document

Upload and process a document for querying.

**Parameters:**
- `content` (string, required): Document content
- `filename` (string, required): File name
- `content_type` (string, required): MIME type

**Example:**
```python
await client.call_tool("upload_document", {
    "content": "This is a financial report...",
    "filename": "report.txt",
    "content_type": "text/plain"
})
```

### 3. get_document_stats

Get statistics about the document collection.

**Parameters:** None

**Example:**
```python
await client.call_tool("get_document_stats", {})
```

**Response:**
```
**Document Collection Statistics**

**Total Documents:** 15
**Total Chunks:** 342
**Total Queries:** 87
**Average Evaluation Score:** 4.1/5.0
```

### 4. search_similar_documents

Find documents similar to a query.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Max results (default: 5)
- `threshold` (number, optional): Similarity threshold (default: 0.7)

**Example:**
```python
await client.call_tool("search_similar_documents", {
    "query": "financial performance",
    "limit": 3,
    "threshold": 0.8
})
```

### 5. get_query_history

Retrieve query history.

**Parameters:**
- `session_id` (string, optional): Filter by session
- `limit` (integer, optional): Max results (default: 10)

**Example:**
```python
await client.call_tool("get_query_history", {
    "session_id": "analysis-session",
    "limit": 5
})
```

### 6. evaluate_response

Evaluate response quality.

**Parameters:**
- `query` (string, required): Original query
- `answer` (string, required): Response to evaluate
- `sources` (array, optional): Source documents

**Example:**
```python
await client.call_tool("evaluate_response", {
    "query": "What is AI?",
    "answer": "Artificial intelligence is...",
    "sources": [{"content": "...", "filename": "ai.pdf"}]
})
```

## Error Handling

The MCP server returns errors in standard JSON-RPC format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Missing required parameter: query"
  }
}
```

Common error codes:
- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## Performance Considerations

### Resource Usage
- **Memory**: ~2GB for vector index and models
- **CPU**: Multi-core recommended for concurrent queries
- **Storage**: Depends on document collection size

### Optimization Tips
1. Use session IDs to track related queries
2. Set appropriate similarity thresholds
3. Limit result counts for better performance
4. Consider caching for frequently accessed documents

## Security

### Authentication
The MCP server runs locally and doesn't require authentication by default. For production:

1. Use environment variables for API keys
2. Implement network-level security
3. Run in isolated containers
4. Monitor access logs

### Data Privacy
- Documents are processed locally
- Only OpenAI API calls are external
- No data is shared beyond configured integrations

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check Python dependencies
   - Verify environment variables
   - Ensure ports are available

2. **Tools not found**
   - Verify server initialization
   - Check tool registration
   - Review server logs

3. **Query failures**
   - Check OpenAI API key
   - Verify document upload
   - Review vector index status

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -m mcp_server.main
```

### Health Checks

The server includes health check endpoints:
- Docker: `docker exec container_name python -c "import mcp_server.main; print('OK')"`
- Local: Check server process and logs

## Integration Examples

### Jupyter Notebook

```python
import asyncio
from mcp_client_example import InsightBotMCPClient

async def notebook_example():
    client = InsightBotMCPClient()
    await client.start_server()
    
    # Upload document
    await client.call_tool("upload_document", {
        "content": open("report.txt").read(),
        "filename": "report.txt",
        "content_type": "text/plain"
    })
    
    # Query
    result = await client.call_tool("query_documents", {
        "query": "Key insights from the report"
    })
    
    print(result)
    await client.close()

# Run in notebook
await notebook_example()
```

### Web Application

```javascript
// Example REST API wrapper for MCP server
async function queryDocuments(query) {
  const response = await fetch('/api/mcp/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ query })
  });
  return response.json();
}
```

## Contributing

To extend the MCP server:

1. Add new tools in `mcp_server/main.py`
2. Update the tool schema
3. Implement the handler function
4. Add tests
5. Update documentation

## Support

For issues and questions:
- Check the logs: `/var/log/supervisor/mcp-server.err.log`
- Review the MCP specification
- Open an issue on GitHub
- Check Docker container health

---

The InsightBot MCP server provides a powerful way to integrate AI-powered document analysis into your applications. Follow this guide to get started and explore the full capabilities of the system.