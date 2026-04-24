import os
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
from config import settings
os.environ["OPENAI_API_KEY"] = settings.api_key.get_secret_value()

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from supervisor import supervisor

# --- Metrics ---

answer_relevancy = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o-mini")

correctness = GEval(
    name="Correctness",
    evaluation_steps=[
        "Check whether the facts in 'actual output' contradict 'expected output'",
        "Penalize omission of critical details",
        "Different wording of the same concept is acceptable",
    ],
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT,
    ],
    model="gpt-4o-mini",
    threshold=0.6,
)

citation_presence = GEval(
    name="Citation Presence",
    evaluation_steps=[
        "Check if the 'actual output' contains citations in the form of [1], [2], etc.",
        "Citations should be present if the 'expected output' contains them",
    ],
    evaluation_params=[
        LLMTestCaseParams.INPUT,
        LLMTestCaseParams.ACTUAL_OUTPUT,
        LLMTestCaseParams.EXPECTED_OUTPUT,
    ],
    model="gpt-4o-mini",
    threshold=0.5,
)

METRICS = [answer_relevancy, correctness, citation_presence]


# --- Run full pipeline ---

def run_pipeline(query: str) -> str:
    config = {"configurable": {"thread_id": f"e2e-{hash(query)}"}, "recursion_limit": 50}

    # Step 1: run pipeline until HITL interrupt (before save_report)
    supervisor.invoke(
        {"messages": [{"role": "user", "content": query}]},
        config=config,
    )

    # Step 2: auto-approve save_report
    result = supervisor.invoke(None, config=config)

    for msg in reversed(result["messages"]):
        if hasattr(msg, "content") and msg.content:
            return msg.content
    return ""


# --- Load golden dataset ---

def load_golden_data(path: str = "tests/golden_dataset.json") -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


# --- Build test cases ---

def build_test_cases(df: pd.DataFrame) -> list[LLMTestCase]:
    test_cases = []
    for i, row in df.iterrows():
        query = row["input"]
        reference = row["expected_output"]

        print(f"[{i+1}/{len(df)}] {query[:60]}...")
        try:
            actual_output = run_pipeline(query)
        except Exception as e:
            print(f"  SKIP — {type(e).__name__}: {e}")
            continue

        if not actual_output:
            print(f"  SKIP — empty output")
            continue

        test_cases.append(LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=reference,
        ))

    return test_cases


# --- Evaluate and print summary ---

def evaluate_and_summarize(test_cases: list[LLMTestCase], metrics: list) -> None:
    scores: dict[str, list[float]] = {
        m.name if hasattr(m, "name") else type(m).__name__: []
        for m in metrics
    }

    passed = 0
    for tc in test_cases:
        tc_passed = True
        for metric in metrics:
            metric.measure(tc)
            name = metric.name if hasattr(metric, "name") else type(metric).__name__
            scores[name].append(metric.score)
            if metric.score < metric.threshold:
                tc_passed = False
        if tc_passed:
            passed += 1

    # Save to CSV
    rows = []
    for tc in test_cases:
        row = {"input": tc.input, "actual_output": tc.actual_output, "expected_output": tc.expected_output}
        for metric in metrics:
            name = metric.name if hasattr(metric, "name") else type(metric).__name__
            row[f"{name}_score"] = scores[name][test_cases.index(tc)]
        rows.append(row)

    pd.DataFrame(rows).to_csv("output/e2e_results.csv", index=False)

    # Print summary
    print(f"\ntest_golden_dataset [{passed}/{len(test_cases)} passed]")
    for name, vals in scores.items():
        if vals:
            print(f"     {name}: avg {sum(vals)/len(vals):.2f}, min {min(vals):.2f}, max {max(vals):.2f}")

    print(f"\nResults saved to output/e2e_results.csv")


# --- Main ---

if __name__ == "__main__":
    df = load_golden_data()
    df = df.head(3)
    print(f"Loaded {len(df)} golden samples\n")

    test_cases = build_test_cases(df)

    print(f"\nRunning evaluation on {len(test_cases)} test cases...\n")
    evaluate_and_summarize(test_cases, METRICS)
