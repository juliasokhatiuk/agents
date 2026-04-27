from dotenv import load_dotenv
load_dotenv()

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from datetime import datetime

class Settings(BaseSettings):
    api_key: SecretStr
    model_name: str = "gpt-5.4-mini"

    hf_token: str | None = None

    # Langfuse observability
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # Web search
    max_search_results: int = 2 #5
    max_url_content_length: int = 2000 #5000

    # RAG
    embedding_model: str = "text-embedding-3-small"
    data_dir: str = "data"
    index_dir: str = "index"
    chunk_size: int = 500
    chunk_overlap: int = 100
    retrieval_top_k: int = 3 #10
    rerank_top_n: int = 3

    # Agent
    output_dir: str = "output"
    max_iterations: int = 50

    model_config = {"env_file": ".env"}

settings = Settings()
