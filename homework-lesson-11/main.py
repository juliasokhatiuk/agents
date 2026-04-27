from supervisor import supervisor
from config import settings
from langgraph.types import Command
from dotenv import load_dotenv
import uuid
import json
from langchain_core.runnables import RunnableConfig
from langfuse import observe, propagate_attributes, get_client
from langfuse.langchain import CallbackHandler

load_dotenv()

langfuse = get_client()
langfuse_handler = CallbackHandler()  # reads LANGFUSE_* env vars

SESSION_ID = f"mas-{uuid.uuid4().hex[:8]}"

AGENT_LABELS = {
    "plan": "Planner",
    "research": "Researcher",
    "critique": "Critic",
    "save_report": "save_report",
}


def _trunc(s, n=80):
    s = str(s)
    return s[:n] + "..." if len(s) > n else s


def print_tool_call(tool_name, args, round_num=None):
    label = AGENT_LABELS.get(tool_name, tool_name)
    round_str = f"  (round {round_num})" if round_num else ""
    print(f"\n[Supervisor -> {label}]{round_str}", flush=True)

    if tool_name == "plan":
        req = args.get("request", str(args))
        print(f'  plan("{_trunc(req)}")', flush=True)
    elif tool_name == "research":
        req = args.get("request", str(args))
        print(f'  research("{_trunc(req)}")', flush=True)
    elif tool_name == "critique":
        findings = args.get("findings", str(args))
        print(f'  critique("[{len(findings)} chars]")', flush=True)
    elif tool_name == "save_report":
        filename = args.get("filename", "?")
        content = args.get("content", "")
        print(f'  save_report(filename="{filename}", content="[{len(content)} chars]")', flush=True)


def print_tool_result(tool_name, content):
    if tool_name == "plan":
        try:
            data = json.loads(content)
            print("  ResearchPlan(", flush=True)
            print(f'    goal="{_trunc(data.get("goal", "?"), 70)}",', flush=True)
            qs = data.get("search_queries", [])
            print(f'    search_queries=[{len(qs)} queries],', flush=True)
            print(f'    sources_to_check={data.get("sources_to_check", [])},', flush=True)
            print(f'    output_format="{_trunc(data.get("output_format", "?"), 60)}"', flush=True)
            print("  )", flush=True)
        except Exception:
            print(f"  {_trunc(content, 200)}", flush=True)

    elif tool_name == "critique":
        try:
            data = json.loads(content)
            verdict = data.get("verdict", "?")
            icon = "APPROVE" if verdict == "APPROVE" else "REVISE"
            print("  CritiqueResult(", flush=True)
            print(f'    verdict="{verdict}" [{icon}],', flush=True)
            print(
                f'    is_fresh={data.get("is_fresh")}, '
                f'is_complete={data.get("is_complete")}, '
                f'is_well_structured={data.get("is_well_structured")},',
                flush=True,
            )
            gaps = data.get("gaps", [])
            if gaps:
                preview = f'"{_trunc(gaps[0], 60)}"' + (", ..." if len(gaps) > 1 else "")
                print(f"    gaps=[{len(gaps)} items: {preview}],", flush=True)
            revs = data.get("revision_requests", [])
            if revs:
                print(f"    revision_requests=[{len(revs)} items]", flush=True)
            print("  )", flush=True)
        except Exception:
            print(f"  {_trunc(content, 200)}", flush=True)

    elif tool_name == "research":
        lines = content.strip().split("\n") if content else []
        print(f"  [Research report: {len(content)} chars, {len(lines)} lines]", flush=True)

    elif tool_name == "save_report":
        print(f"  {content}", flush=True)


def run_stream(input_or_command, config):
    """Stream supervisor with formatted output. Returns (interrupted, interrupt_args)."""
    interrupted = False
    interrupt_args = {}
    research_count = [0]
    critique_count = [0]
    # phase-1: collect args from model node keyed by tool_call_id (no printing)
    pending_calls: dict = {}
    # phase-2: print header+result from tools node, dedup by tool_call_id
    seen_tool_result_ids: set = set()

    for chunk in supervisor.stream(
        input_or_command,
        config=config,
        stream_mode=["updates", "messages"],
        version="v2",
    ):
        chunk_type = chunk.get("type")

        if chunk_type == "messages":
            token, _ = chunk["data"]
            # skip tool messages — shown via updates/tools
            if type(token).__name__ in ("ToolMessage", "ToolMessageChunk"):
                continue
            # skip AI messages that contain tool calls — shown via updates/tools
            if getattr(token, "tool_calls", None) or getattr(token, "tool_call_chunks", None):
                continue
            if token.content:
                print(token.content, end="", flush=True)

        elif chunk_type == "updates":
            data = chunk["data"]

            for node_name, node_data in data.items():

                if node_name == "__interrupt__":
                    interrupted = True
                    try:
                        action = node_data[0].value["action_requests"][0]
                        interrupt_args = {"name": action["name"], "args": dict(action["args"])}
                    except Exception:
                        pass
                    args = interrupt_args.get("args", {})
                    print("\n", flush=True)
                    print("=" * 60, flush=True)
                    print("  ACTION REQUIRES APPROVAL", flush=True)
                    print("=" * 60, flush=True)
                    print(f'  Tool:  {interrupt_args.get("name", "save_report")}', flush=True)
                    print(f'  File:  {args.get("filename", "?")}', flush=True)
                    print(f'  Size:  {len(args.get("content", ""))} chars', flush=True)
                    print("=" * 60, flush=True)

                elif node_name == "model":
                    # Phase 1: collect tool call args without printing
                    for msg in node_data.get("messages", []):
                        for tc in getattr(msg, "tool_calls", []):
                            tc_id = tc.get("id") or tc.get("tool_call_id")
                            if not tc_id or tc_id in pending_calls:
                                continue
                            tname = tc["name"]
                            rnum = None
                            if tname == "research":
                                research_count[0] += 1
                                rnum = research_count[0]
                            elif tname == "critique":
                                critique_count[0] += 1
                                rnum = critique_count[0]
                            pending_calls[tc_id] = {
                                "name": tname,
                                "args": tc.get("args", {}),
                                "rnum": rnum,
                            }

                elif node_name == "tools":
                    # Phase 2: print header+result once per tool_call_id
                    for msg in node_data.get("messages", []):
                        tname = getattr(msg, "name", None)
                        if not tname:
                            continue
                        tc_id = getattr(msg, "tool_call_id", None) or getattr(msg, "id", None)
                        if tc_id and tc_id in seen_tool_result_ids:
                            continue
                        if tc_id:
                            seen_tool_result_ids.add(tc_id)
                        call_info = pending_calls.get(tc_id, {})
                        print_tool_call(
                            call_info.get("name", tname),
                            call_info.get("args", {}),
                            call_info.get("rnum"),
                        )
                        content = getattr(msg, "content", "")
                        print_tool_result(tname, content)

    return interrupted, interrupt_args


def handle_interrupt(interrupt_args: dict, config: dict) -> None:
    """Loop until the current HITL interrupt is fully resolved."""
    while True:
        user_action = input("\nAction (approve / edit / reject): ").strip().lower()

        if user_action == "approve":
            filename = interrupt_args.get("args", {}).get("filename", "output file")
            interrupted, new_args = run_stream(
                Command(resume={"decisions": [{"type": "approve"}]}), config
            )
            print(f"\n  Approved! Report saved to output/{filename}", flush=True)
            if interrupted:
                interrupt_args = new_args
                continue
            return

        elif user_action == "edit":
            feedback = input("  Your feedback: ").strip()
            print("\n[Supervisor revises report based on feedback]", flush=True)
            interrupted, interrupt_args = run_stream(
                Command(resume={"decisions": [{"type": "reject", "message": f"REVISE: {feedback}"}]}),
                config,
            )
            if interrupted:
                # Supervisor produced a revised save_report — loop back to ask again
                continue
            return

        elif user_action == "reject":
            reason = input("  Reason: ").strip()
            run_stream(
                Command(resume={"decisions": [{"type": "reject", "message": reason}]}),
                config,
            )
            return

        else:
            print("Unknown action. Valid: approve / edit / reject", flush=True)


@observe(name="mas-research-run")
def run_query(user_input: str) -> None:
    trace_id = langfuse.get_current_trace_id()
    with propagate_attributes(
        session_id=SESSION_ID,
        user_id="user",
        tags=["mas", "research"],
        metadata={"model": settings.model_name},
    ):
        config = RunnableConfig(
            callbacks=[langfuse_handler],
            recursion_limit=settings.max_iterations,
            configurable={"thread_id": SESSION_ID},
        )

        interrupted, interrupt_args = run_stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
        )

        if not interrupted:
            print("\nSupervisor finished without interrupt.", flush=True)
        else:
            handle_interrupt(interrupt_args, config)

    print(f"\n🆔 trace_id: {trace_id}", flush=True)
    langfuse.flush()


def main():
    print("Multi-agent research system (type 'exit' to quit)")
    print(f"Session: {SESSION_ID}")
    print("-" * 40)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        run_query(user_input)


if __name__ == "__main__":
    main()
