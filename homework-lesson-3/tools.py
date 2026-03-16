from langchain_core.tools import tool
from ddgs import DDGS
import trafilatura
import os
from pathlib import Path
from config import Settings

settings = Settings()


@tool
def web_search(query: str) -> list[dict]:

    """Use this tool to web search for the given query and return a list of results with title, url, and snippet"""

    max_results = settings.max_search_results
   
    try:
        results = DDGS().text(query, max_results=max_results) 
        return [
            {
               "title": r.get("title"),
               "link": r.get("href"),
               "snippet": r.get("body")
            }
            for r in results
        ]
    except Exception as e:
        return f"Error: Web search failed. {str(e)}"



@tool
def read_url(url: str) -> str:

    """ Downloads and extracts text content from a URL, returning a truncated version if it exceeds max_chars"""
    
    max_chars = settings.max_url_content_length
    
    if not url.startswith(("http://", "https://")):
        return f"Error: Invalid URL format. The URL must start with http:// or https://. Received: {url}"

    try:
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            return f"Error: The page at {url} is inaccessible (404, 403, or Timeout)."
        
        text = trafilatura.extract(downloaded)

        if not text:
            return f"Error: Successfully reached {url}, but could not extract any meaningful text content."
        
        if len(text) > max_chars:
            return text[:max_chars]+"..."
        
        return text

    except Exception as e:
        return f"Error: Failed to fetch URL. {str(e)}"



@tool
def write_report(filename: str, content: str) -> str:
    
    """Saves a report in Markdown format to the directory specified in settings."""

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