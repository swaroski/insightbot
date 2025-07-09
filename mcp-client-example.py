#!/usr/bin/env python3
"""
Example MCP client for InsightBot
Demonstrates how to interact with the MCP server
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any

class InsightBotMCPClient:
    """Simple MCP client for InsightBot"""
    
    def __init__(self, server_command: list = None):
        self.server_command = server_command or [
            "python", "-m", "mcp_server.main"
        ]
        self.process = None
    
    async def start_server(self):
        """Start the MCP server process"""
        self.process = await asyncio.create_subprocess_exec(
            *self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Send initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "InsightBot MCP Client",
                    "version": "1.0.0"
                }
            }
        }
        
        await self._send_request(init_request)
        response = await self._read_response()
        
        if response.get("error"):
            raise Exception(f"Initialization failed: {response['error']}")
        
        print("✅ MCP Server initialized successfully")
        return response
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        await self._send_request(request)
        response = await self._read_response()
        
        if response.get("error"):
            raise Exception(f"List tools failed: {response['error']}")
        
        return response.get("result", {})
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_request(request)
        response = await self._read_response()
        
        if response.get("error"):
            raise Exception(f"Tool call failed: {response['error']}")
        
        return response.get("result", {})
    
    async def _send_request(self, request: Dict[str, Any]):
        """Send a JSON-RPC request to the server"""
        if not self.process:
            raise Exception("Server not started")
        
        message = json.dumps(request) + "\n"
        self.process.stdin.write(message.encode())
        await self.process.stdin.drain()
    
    async def _read_response(self) -> Dict[str, Any]:
        """Read a JSON-RPC response from the server"""
        if not self.process:
            raise Exception("Server not started")
        
        line = await self.process.stdout.readline()
        if not line:
            raise Exception("No response from server")
        
        try:
            return json.loads(line.decode().strip())
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
    
    async def close(self):
        """Close the connection to the server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()

async def main():
    """Main demonstration of MCP client usage"""
    client = InsightBotMCPClient()
    
    try:
        # Start the server
        print("🚀 Starting MCP server...")
        await client.start_server()
        
        # List available tools
        print("\n📋 Listing available tools...")
        tools_result = await client.list_tools()
        tools = tools_result.get("tools", [])
        
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Example 1: Upload a document
        print("\n📤 Uploading a sample document...")
        upload_result = await client.call_tool("upload_document", {
            "content": "This is a sample document about artificial intelligence and machine learning.",
            "filename": "sample.txt",
            "content_type": "text/plain"
        })
        
        print("Upload result:")
        for content in upload_result.get("content", []):
            print(content["text"])
        
        # Example 2: Query documents
        print("\n🔍 Querying documents...")
        query_result = await client.call_tool("query_documents", {
            "query": "What is artificial intelligence?",
            "session_id": "demo-session"
        })
        
        print("Query result:")
        for content in query_result.get("content", []):
            print(content["text"])
        
        # Example 3: Get document stats
        print("\n📊 Getting document statistics...")
        stats_result = await client.call_tool("get_document_stats", {})
        
        print("Document stats:")
        for content in stats_result.get("content", []):
            print(content["text"])
        
        # Example 4: Search similar documents
        print("\n🔎 Searching for similar documents...")
        search_result = await client.call_tool("search_similar_documents", {
            "query": "machine learning",
            "limit": 3
        })
        
        print("Search result:")
        for content in search_result.get("content", []):
            print(content["text"])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        await client.close()
    
    print("\n✅ MCP client demo completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))