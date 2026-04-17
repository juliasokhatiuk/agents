# python -m mcp_servers.search_mcp

from fastmcp import Client
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

async def test_mcp_server():
    async with Client("http://127.0.0.1:8902/mcp") as client:
        # 1. List available tools
        tools = await client.list_tools()
        print('-' * 50)
        print("Available Tools:")
        for t in tools: print(f"   - {t.name}: {(t.description or '')}")
        print()

        # 2. List available resources
        resources = await client.list_resources()
        print('-' * 50)
        print("Available Resources:")
        for r in resources: print(f"   - {r.uri}: {r.name}")
        print()

        # 3. Read a specific resource     
        print('-' * 50)
        print("resource://output-dir:") 
        output_dir = await client.read_resource("resource://output-dir")
        print(f" {output_dir}")

       
asyncio.run(test_mcp_server())

# python test_report_mcp.py

# Available Tools:
#    - web_search: Search the web for the given query. Returns a JSON string with results (title, link, snippet).
#    - read_url: Downloads and extracts full text content from a URL. Use when a search snippet is not enough and you need the 
# full page content.
#    - knowledge_search: Search the local knowledge base using hybrid retrieval + reranking.

# --------------------------------------------------
# Available Resources:
#    - resource://knowledge-base-stats: get_knowledge_base_stats

# --------------------------------------------------
# resource://knowledge-base-stats:
#  [TextResourceContents(uri=AnyUrl('resource://knowledge-base-stats'), mimeType='text/plain', meta=None, text='{"total_documents": 3, "documents": ["langchain.pdf", "large-language-model.pdf", "retrieval-augmented-generation.pdf"], "total_chunks": 225, "last_updated": "2026-03-20 15:01:53"}')]

