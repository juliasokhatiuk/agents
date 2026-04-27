from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from agents.planner import planner_agent
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
os.environ["OPENAI_API_KEY"] = settings.api_key.get_secret_value()

plan_quality = GEval(
    name="Plan Quality",
    evaluation_steps=[
        "Check that the plan contains specific search queries (not vague)",
        "Check that sources_to_check includes relevant sources for the topic",
        "Check that the output_format matches what the user asked for",
    ],
    evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    model="gpt-5.4-mini",
    threshold=0.7,
)

TEST_QUERIES = [
    "Compare naive RAG with hybrid retrieval and reranking.",
    "How does RAG reduce hallucinations, and why does it still not eliminate them?",
    "Summarize the main stages of a RAG pipeline from chunking to final answer generation.",
]

def test_planner(query: str) -> str:
    result = planner_agent.invoke({"message": [{"role": "user", "content": query}]})
    plan = result["structured_response"]
    return plan.model_dump_json()


if __name__ == "__main__":
    test_cases = [LLMTestCase(input=query, actual_output=test_planner(query)) for query in TEST_QUERIES]

    evaluate(test_cases,metrics=[plan_quality])

    
# Query: Summarize the main stages of a RAG pipeline from chunking to final answer generation.
# Score: 0.2
# Reason: The response includes specific search queries, but they are about clarifying a research topic rather than the requested RAG pipeline 
