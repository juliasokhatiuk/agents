import json
import os
from config import Settings
from ddgs import DDGS
import trafilatura
from pathlib import Path

settings = Settings()

# web_search.args_schema.model_json_schema()

web_search_tool_schema = {
    "type": "function",
    "name": "web_search",
    "description": "Search the web for the given query. Returns a JSON string with results (title, link, snippet)",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to look up on the web"
            }
        },
        "required": ["query"]
    }
}


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




read_url_tool_schema = {
    "type": "function",
    "name": "read_url",
    "description": "Downloads and extracts full text content from a URL. Use when a search snippet is not enough and you need the full page content.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Full URL to fetch, must start with http:// or https://"
            }
        },
        "required": ["url"]
    }
}

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


write_report_tool_schema = {
    "type": "function",
    "name": "write_report",
    "description": "Saves the final research report as a Markdown file. Always call this tool last, after collecting and analysing all information.",
    "parameters": {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Name of the file to save, e.g. 'rag_comparison.md'. .md extension will be added automatically if missing."
            },
            "content": {
                "type": "string",
                "description": "Full Markdown content of the report."
            }
        },
        "required": ["filename", "content"]
    }
}

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