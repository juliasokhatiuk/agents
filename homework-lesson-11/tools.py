from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
import json
import os
from config import settings
from ddgs import DDGS
import trafilatura
from pathlib import Path
from retriever import get_retriever
from schemas import ResearchPlan, CritiqueResult


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
def save_report(filename: str, content: str) -> str:
    
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


retriever = get_retriever()

@tool
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


@tool
def plan(request: str, config: RunnableConfig) -> ResearchPlan:
    """Generate a structured research plan based on the user's request."""

    from agents.planner import planner_agent

    result = planner_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"configurable": {}, "callbacks": config.get("callbacks")},
    )

    return result["structured_response"].model_dump()


MAX_RESEARCH_INPUT = 3000  # chars — prevent huge gap lists from bloating the research request

@tool
def research(request: str, config: RunnableConfig) -> str:
    """Research a topic using local knowledge and web sources, then return a structured Markdown report."""

    from agents.research import research_agent

    if len(request) > MAX_RESEARCH_INPUT:
        request = request[:MAX_RESEARCH_INPUT] + "\n\n[...truncated...]"

    result = research_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        config={"configurable": {}, "callbacks": config.get("callbacks")},
    )

    return result["messages"][-1].content

MAX_CRITIQUE_INPUT = 10000  # chars — enough to see the full report structure

@tool
def critique(findings: str, config: RunnableConfig) -> CritiqueResult:
    """Critically evaluate the research findings and suggest improvements."""

    from agents.critic import critic_agent

    # Extract only the latest research block — strip any previously appended
    # critique feedback that the supervisor may have included in the findings string.
    marker = "=== LATEST RESEARCH ==="
    if marker in findings:
        latest = findings.split(marker)[-1].strip()
    else:
        latest = findings.strip()

    # Truncate to avoid exceeding context window
    if len(latest) > MAX_CRITIQUE_INPUT:
        latest = latest[:MAX_CRITIQUE_INPUT] + "\n\n[...truncated for length...]"

    result = critic_agent.invoke(
        {"messages": [{"role": "user", "content": latest}]},
        config={"configurable": {}, "callbacks": config.get("callbacks")},
    )

    return result["structured_response"].model_dump()
