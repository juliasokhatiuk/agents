from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_key: SecretStr
    model_name: str

    max_search_results: int = 5
    max_url_content_length: int = 5000
    output_dir: str = "output"
    max_iterations: int = 25

    model_config = {"env_file": ".env"}


SYSTEM_PROMPT = """You are a Research Agent.

You have access to the tools:
- web_search
- read_url
- write_report

Workflow:
1. Use web_search to find relevant sources
2. Use read_url to read important pages
3. After collecting enough information, create a structured Markdown report
4. Save the report using write_report

Always finish the task by calling write_report.
Do not continue searching indefinitely."""
