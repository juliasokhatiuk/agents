from fastmcp import FastMCP
from config import settings
import json
import os
from datetime import datetime
from pathlib import Path


mcp_server = FastMCP(name="ReportMCP")

@mcp_server.tool
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



@mcp_server.resource("resource://output-dir")
def get_output_dir() -> str:
    """шлях до директорії та список збережених звітів"""

    output_dir = Path(settings.output_dir).absolute()

    if not output_dir.exists():
        return json.dumps({
            "status": "empty",
            "path": str(output_dir),
            "reports": [],
            "total_reports": 0,
        })

    reports = sorted(output_dir.glob("*.md"))

    return json.dumps({
        "status": "ready",
        "path": str(output_dir),
        "total_reports": len(reports),
        "reports": [
            {
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "last_modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for f in reports
        ],
    })

if __name__ == "__main__":
    mcp_server.run(transport="streamable-http", host="127.0.0.1", port=8902)