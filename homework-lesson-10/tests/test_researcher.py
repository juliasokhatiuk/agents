from deepeval import evaluate
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from agents.research import research_agent
import os
from dotenv import load_dotenv
load_dotenv()
from config import settings
os.environ["OPENAI_API_KEY"] = settings.api_key.get_secret_value()


groundedness = GEval(
    name="Groundedness",
    evaluation_steps=[
        "Extract every factual claim from 'actual output'",
        "For each claim, check if it can be directly supported by 'retrieval context'",
        "Claims not present in retrieval context count as ungrounded, even if true",
        "Score = number of grounded claims / total claims",
    ],
    evaluation_params=[
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.RETRIEVAL_CONTEXT,
    ],
    model="gpt-5.4-mini",
    threshold=0.7,
)

TEST_CASES = [
    {
        "input": """Based only on the research notes below, write a concise Markdown report that compares naive RAG, hybrid retrieval, and reranking. Do not add facts that are not explicitly stated in the notes.

Research notes:
- Naive RAG uses a single dense retrieval step over fixed-size chunks.
- Hybrid retrieval combines dense retrieval with BM25 lexical search, which improves recall for both semantic meaning and exact terms.
- Reranking applies a cross-encoder to rescore the top retrieved chunks and improve precision.
- Hybrid retrieval plus reranking usually produces better answer quality than naive RAG, but it adds latency and system complexity.
""",
        "retrieval_context": [
            "Naive RAG uses a single dense retrieval step over fixed-size chunks.",
            "Hybrid retrieval combines dense retrieval with BM25 lexical search and improves recall for both semantic meaning and exact terms.",
            "Reranking applies a cross-encoder to rescore the top retrieved chunks and improve precision.",
            "Hybrid retrieval plus reranking usually produces better answer quality than naive RAG, but it adds latency and system complexity.",
        ],
    },
    {
        "input": """Based only on the research notes below, explain how RAG reduces hallucinations and why it still cannot eliminate them. Return a short Markdown report and avoid adding outside information.

Research notes:
- RAG reduces hallucinations by grounding the model on retrieved external documents instead of relying only on parametric memory.
- Retrieved context can still be incomplete, irrelevant, or outdated.
- If retrieval misses the needed evidence, the model may still guess or overgeneralize.
- The generation step can still introduce unsupported claims even when some context is correct.
""",
        "retrieval_context": [
            "RAG reduces hallucinations by grounding the model on retrieved external documents instead of relying only on parametric memory.",
            "Retrieved context can still be incomplete, irrelevant, or outdated.",
            "If retrieval misses the needed evidence, the model may still guess or overgeneralize.",
            "The generation step can still introduce unsupported claims even when some context is correct.",
        ],
    },
    {
        "input": """Using only the notes below, summarize the main stages of a RAG pipeline from chunking to final answer generation. Keep the answer concise and grounded strictly in the notes.

Research notes:
- Chunking splits source documents into smaller passages, sometimes with overlap.
- Embedding converts each chunk into a vector representation for indexing.
- Retrieval selects the most relevant chunks for a user query.
- Reranking reorders the retrieved candidates to keep the most useful passages near the top.
- Generation combines the user query with the selected context to produce the final answer.
""",
        "retrieval_context": [
            "Chunking splits source documents into smaller passages, sometimes with overlap.",
            "Embedding converts each chunk into a vector representation for indexing.",
            "Retrieval selects the most relevant chunks for a user query.",
            "Reranking reorders the retrieved candidates to keep the most useful passages near the top.",
            "Generation combines the user query with the selected context to produce the final answer.",
        ],
    },
]



def run_research(prompt: str) -> str:
    result = research_agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]}
    )

    return result["messages"][-1].content


if __name__ == "__main__":
    test_cases = [
        LLMTestCase(
            input=item["input"],
            actual_output=run_research(item["input"]),
            retrieval_context=item["retrieval_context"],
        )
        for item in TEST_CASES
    ]
    evaluate(test_cases, [groundedness])



# Metrics Summary

#   - ✅ Groundedness [GEval] (score: 0.8, threshold: 0.7, strict: False, evaluation model: gpt-5.4-mini, reason: Most claims are directly suppo
# rted by the retrieval context: RAG grounding reduces hallucinations, retrieved context may be incomplete/irrelevant/outdated, missed evidence can lead to guessing or overgeneralizing, and generation can still add unsupported claims. However, several added details are not explicitly in the context, such as "parametric-only generation" being prone to inventing facts, "two separate failure modes," and the broader comparison framing, so not every factual claim is grounded., error: None)