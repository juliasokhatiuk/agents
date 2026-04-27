from deepeval.test_case import LLMTestCase, ToolCall
from deepeval.metrics import ToolCorrectnessMetric
from deepeval import evaluate
from langchain_core.messages import AIMessage

from agents.planner import planner_agent
from agents.research import research_agent
from supervisor import supervisor
from langchain_core.messages import AIMessage

from schemas import ResearchPlan
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
os.environ["OPENAI_API_KEY"] = settings.api_key.get_secret_value()



TEST_QUERIES = [
    "Compare naive RAG with hybrid retrieval and reranking.",
    "How does RAG reduce hallucinations, and why does it still not eliminate them?",
    "Summarize the main stages of a RAG pipeline from chunking to final answer generation.",
]


TEST_PLANS = [
    ResearchPlan(
        goal="Compare naive RAG with hybrid retrieval and reranking.",
        search_queries=["naive RAG vs hybrid retrieval", "reranking techniques RAG"],
        sources_to_check=["knowledge_base"],
        output_format="Comparison table and key takeaways",
    ),
    ResearchPlan(
        goal="How does RAG reduce hallucinations?",
        search_queries=["RAG hallucination reduction"],
        sources_to_check=["web"],
        output_format="Summary with sources",
    ),
    ResearchPlan(
        goal="Summarize the main stages of a RAG pipeline.",
        search_queries=["RAG pipeline stages chunking embedding retrieval generation"],
        sources_to_check=["both"],
        output_format="Step-by-step summary",
    ),
]

SUPERVISOR_INPUT = """User request: Compare naive RAG with hybrid retrieval.

Research findings:
# RAG Approaches Comparison
Hybrid retrieval outperforms naive RAG for technical queries.

Critique verdict: APPROVE
"""



def tools_called(result: dict) -> list[ToolCall]:
    return [
        ToolCall(name=tc["name"])
        for msg in result.get("messages", [])
        if isinstance(msg, AIMessage)
        for tc in (msg.tool_calls or [])
    ]



tool_metric = ToolCorrectnessMetric(threshold=0.5, model="gpt-5.4-mini")


planner_expected_tools = [ToolCall(name="web_search"), ToolCall(name="knowledge_search")]

def run_planner_tools(query: str) -> tuple[str, list[ToolCall]]:
    result = planner_agent.invoke({"messages": [{"role": "user", "content": query}]})
    plan = result["structured_response"]

    return plan.model_dump_json(), tools_called(result)



SOURCES_TO_TOOLS = {
    "knowledge_base": [ToolCall(name="knowledge_search")],
    "web": [ToolCall(name="web_search"), ToolCall(name="read_url")],
    "both": [
        ToolCall(name="knowledge_search"),
        ToolCall(name="web_search"),
        ToolCall(name="read_url"),
    ],
}

def run_researcher_tools(plan: ResearchPlan) -> tuple[str, list[ToolCall]]:
    input_text = plan.model_dump_json()
    result = research_agent.invoke({"messages": [{"role": "user", "content": input_text}]})

    actual_tools = tools_called(result)

    expected = [
    tool
    for src in plan.sources_to_check
    if src in SOURCES_TO_TOOLS
    for tool in SOURCES_TO_TOOLS[src]
]

    output = result["messages"][-1].content
    return output, actual_tools, expected

def run_supervisor_tools(input_text: str) -> tuple[str, list[ToolCall]]:
    config = {"configurable": {"thread_id": "test-supervisor"}}

    # Перший invoke — supervisor планує і зупиняється перед save_report
    result = supervisor.invoke({"messages": [{"role": "user", "content": input_text}]}, config=config)

    # Другий invoke — supervisor отримує APPROVE і викликає save_report
    result = supervisor.invoke(None, config=config)

    actual_tools = tools_called(result)
    output = result["messages"][-1].content
    return output, actual_tools

def make_case(input_text, output, actual, expected):
    return LLMTestCase(
        input=input_text,
        actual_output=output,
        tools_called=actual,
        expected_tools=expected,
    )

if __name__ == "__main__":
    test_cases = []

    # Planner: перевіряємо що викликає пошукові інструменти
    for query in TEST_QUERIES:
        output, tools = run_planner_tools(query)
        test_cases.append(make_case(query, output, tools, planner_expected_tools))




    # Researcher: перевіряємо що викликає інструменти згідно з планом
    for plan in TEST_PLANS:
        output, actual_tools, expected = run_researcher_tools(plan)
        test_cases.append(make_case(plan.model_dump_json(), output, actual_tools, expected))

  

    # Supervisor отримує APPROVE від Critic → має викликати save_report
    output, actual_tools = run_supervisor_tools(SUPERVISOR_INPUT)
    test_cases.append(make_case(
    SUPERVISOR_INPUT,
    output,
    actual_tools,
    [ToolCall(name="save_report")],
))
    
    evaluate(test_cases, metrics=[tool_metric])

