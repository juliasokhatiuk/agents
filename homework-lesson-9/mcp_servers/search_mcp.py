from fastmcp import FastMCP
from config import settings
from ddgs import DDGS
import json
import os
import trafilatura
from retriever import get_retriever
import json, os
from datetime import datetime

mcp_server = FastMCP(name="SearchMCP")


# MCP Server: Define Tools (actions with side effects)
@mcp_server.tool
def web_search(query: str) -> str:
    """
    Search the web for the given query. Returns a JSON string with results (title, link, snippet).
    """
    max_results = settings.max_search_results
    max_chars = settings.max_url_content_length

    try:
        results = DDGS().text(query, max_results=max_results)

        output = []
        total_length = 0

        for r in results:
            item = {
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", "")
            }

            item_str = json.dumps(item)
            item_len = len(item_str)

            # якщо перевищуємо ліміт — зупиняємось
            if total_length + item_len > max_chars:
                break

            output.append(item)
            total_length += item_len

        return json.dumps({
            "status": "success",
            "results": output
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Web search failed: {str(e)}"
        })
    

@mcp_server.tool
def read_url(url: str) -> str:
    """
    Downloads and extracts full text content from a URL. Use when a search snippet is not enough and you need the full page content.
    """
    max_chars = settings.max_url_content_length

    if not url.startswith(("http://", "https://")):
        return json.dumps({
            "status": "error",
            "message": f"Invalid URL format: {url}"
        })

    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return json.dumps({
                "status": "error",
                "message": f"The page at {url} is inaccessible (404, 403, or Timeout)."
            })

        text = trafilatura.extract(downloaded)
        if not text:
            return json.dumps({
                "status": "error",
                "message": f"Could not extract any meaningful text content."
            })

        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        return json.dumps({
            "status": "success",
            "url": url,
            "content": text
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to fetch URL: {str(e)}"
        })


retriever = get_retriever()

@mcp_server.tool
def knowledge_search(query: str) -> str:
    """Search the local knowledge base using hybrid retrieval + reranking."""
    
    docs = retriever.invoke(query)

    if not docs:
        return json.dumps({"status": "empty", "message": "No relevant documents found."})

    results = []
    for doc in docs:
        results.append({
            "page": doc.metadata.get("page_label", "?"),
            "file": doc.metadata.get("file_name", "?"),
            "content": doc.page_content
        })

    return json.dumps({"status": "success", "results": results})


# MCP Server: Define Resources (read-only data)

@mcp_server.resource("resource://knowledge-base-stats")
def get_knowledge_base_stats() -> str:
    """Return knowledge base stats: document count, total chunks, and last updated date."""
    

    chunks_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "index", "chunks.json")
    )

    if not os.path.exists(chunks_path):
        return json.dumps({
            "status": "not_ready",
            "message": "Knowledge base is empty. Run ingest.py first.",
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None,
        }, ensure_ascii=False)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    unique_docs = {
        chunk["metadata"]["file_name"]
        for chunk in chunks
        if chunk.get("metadata", {}).get("file_name")
    }

    last_updated = datetime.fromtimestamp(
        os.path.getmtime(chunks_path)
    ).strftime("%Y-%m-%d %H:%M:%S")

    return json.dumps({
        "total_documents": len(unique_docs),
        "documents": sorted(unique_docs),
        "total_chunks": len(chunks),
        "last_updated": last_updated,
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp_server.run(transport="streamable-http", host="127.0.0.1", port=8901)