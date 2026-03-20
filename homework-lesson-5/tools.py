from langchain.tools import tool
import json
import os
from config import Settings
from ddgs import DDGS
import trafilatura
from pathlib import Path
from retriever import get_retriever

settings = Settings()

@tool
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

@tool
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


@tool
def write_report(filename: str, content: str) -> str:
    
    """Saves the final research report as a Markdown file. Always call this tool last, after collecting and analysing all information."""

    try:
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        clean_filename = Path(filename).name

        if not clean_filename.endswith('.md'):
            clean_filename += '.md'
            
        file_path = output_dir / clean_filename

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)

        full_path = os.path.abspath(file_path)

        return f"Report successfully saved to {file_path.absolute()}"
    
    except Exception as e:
        return f"Error: Failed to save report. {str(e)}"



@tool
def knowledge_search(query: str) -> str:
    """Search the local knowledge base using hybrid retrieval + reranking."""
    
    retriever = get_retriever()
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

