"""Builder for Lab 06 — Trust: Observability & Evaluation."""
from nb_util import md, code, save

BOOTSTRAP = '''
import sys, os, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
here = Path.cwd()
src = next((p / "src" for p in [here, *here.parents] if (p / "src" / "config.py").exists()), None)
if src and str(src) not in sys.path:
    sys.path.insert(0, str(src))

import config
'''

cells = [
    md("""
# Lab 06 · Trust — Observability & Evaluation

A copilot that gives field technicians safety guidance must be **trustworthy**.
Two disciplines make that possible:

- **Observability** — capture every interaction (prompt, response, latency, tool
  calls) as traces you can audit and debug.
- **Evaluation** — score the agent's answers against quality criteria so you can
  catch regressions *before* they reach the field.

This lab does both against a grounded copilot.

> 🧭 **Prerequisite:** run **Lab 04** first — this lab evaluates the Azure AI
> Search–grounded agent and reuses that index.

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## Part A · Observability with tracing

We route traces to the project's **Application Insights** resource via
OpenTelemetry. Setting `AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED=true`
records the full prompt/response content (an audit trail).
"""),
    code(BOOTSTRAP + '''
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import format_trace_id

project_client = config.get_project_client()
conn_str = project_client.telemetry.get_application_insights_connection_string()
configure_azure_monitor(connection_string=conn_str)
tracer = trace.get_tracer("schneider-technician-copilot")
print("✅ Tracing configured -> Application Insights")
'''),
    md("""
### Create a grounded agent and trace its calls

We wrap each interaction in a custom span with business attributes (site, category)
— exactly what you'd audit later for a safety-critical field action.
"""),
    code('''
from azure.ai.projects.models import (
    AzureAISearchTool, AzureAISearchToolResource, AISearchIndexResource, AzureAISearchQueryType,
)

search_conn = config.get_search_connection(project_client)
search_tool = AzureAISearchTool(
    azure_ai_search=AzureAISearchToolResource(
        indexes=[AISearchIndexResource(
            project_connection_id=search_conn.name,
            index_name=config.WORKSHOP_INDEX_NAME,
            query_type=AzureAISearchQueryType.SEMANTIC,
        )]
    )
)
eval_agent = config.create_prompt_agent(
    project_client,
    name="technician-copilot-observed",
    instructions=config.TECH_PERSONA + "\\n\\nYou MUST call the Azure AI Search tool "
    "to consult the product manuals before answering ANY question about fault codes, "
    "specifications, safety, or procedures. Never answer a fault code from memory. "
    "Base your answer on the retrieved manual text and cite the source. If the search "
    "returns nothing relevant, say so.",
    tools=[search_tool],
)
print("✅ Grounded agent:", eval_agent.name)

def traced_ask(question, site="SITE-CHN-01", category="fault-code"):
    with tracer.start_as_current_span("technician_query") as span:
        span.set_attribute("site.id", site)
        span.set_attribute("query.category", category)
        span.set_attribute("agent.name", eval_agent.name)
        answer = config.ask(project_client, eval_agent, question)
        span.set_attribute("response.length", len(answer))
        print("Trace ID:", format_trace_id(span.get_span_context().trace_id))
        return answer

print("🤖", traced_ask("A Galaxy VS UPS shows E07. What is the first action?")[:300], "...")
'''),
    code('''
print("🤖", traced_ask(
    "On a MasterPact MTZ, what does TU-14 mean?", category="safety")[:300], "...")
'''),
    md("""
### Where to view the traces

1. **Foundry portal → Tracing** — search by the printed Trace ID.
2. **Application Insights → Transaction search** — filter by the role name
   `schneider-technician-copilot`.

Traces may take 1-3 minutes to appear. Each shows the prompt, the tool/search
calls, the response, and latency — a complete audit trail.
"""),
    md("""
## Part B · Evaluation

We score the copilot with Foundry's server-side **evals**. Each test query is run
through the agent and graded by built-in evaluators:

- **`relevance`** — does the answer actually address the technician's question?
- **`coherence`** — is the reasoning logically consistent and easy to follow?
- **`fluency`** — is the answer clear and well-formed?

We draw the questions from our ground-truth set `data/eval/technician_qa.jsonl`.
One question (`qa-12`) is deliberately **out of scope** — watch its `relevance`
score drop, which is exactly the signal you want evaluation to surface.
"""),
    code('''
import json

qa_rows = [json.loads(l) for l in config.EVAL_QA_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
# Use a representative subset to keep the run quick.
subset = [r for r in qa_rows if r["id"] in ("qa-01", "qa-05", "qa-06", "qa-11", "qa-12")]
test_queries = [{"item": {"query": r["question"]}} for r in subset]
print(f"Evaluating {len(test_queries)} questions:")
for r in subset:
    print(f"  [{r['category']}] {r['question'][:60]}")
'''),
    code('''
from openai.types.eval_create_params import DataSourceConfigCustom

openai_client = project_client.get_openai_client()

data_source_config = DataSourceConfigCustom(
    type="custom",
    item_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    include_sample_schema=True,
)
testing_criteria = [
    {
        "type": "azure_ai_evaluator", "name": "relevance",
        "evaluator_name": "builtin.relevance",
        "initialization_parameters": {"deployment_name": config.MODEL},
        "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
    },
    {
        "type": "azure_ai_evaluator", "name": "coherence",
        "evaluator_name": "builtin.coherence",
        "initialization_parameters": {"deployment_name": config.MODEL},
        "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
    },
    {
        "type": "azure_ai_evaluator", "name": "fluency",
        "evaluator_name": "builtin.fluency",
        "initialization_parameters": {"deployment_name": config.MODEL},
        "data_mapping": {"query": "{{item.query}}", "response": "{{sample.output_text}}"},
    },
]
eval_object = openai_client.evals.create(
    name="Schneider Technician Copilot Evaluation",
    data_source_config=data_source_config,
    testing_criteria=testing_criteria,
)
print("✅ Eval created:", eval_object.id)
'''),
    code('''
import time

data_source = {
    "type": "azure_ai_target_completions",
    "source": {"type": "file_content", "content": test_queries},
    "input_messages": {"type": "template", "template": [
        {"type": "message", "role": "user",
         "content": {"type": "input_text", "text": "{{item.query}}"}}
    ]},
    "target": {"type": "azure_ai_agent", "name": eval_agent.name},
}
run = openai_client.evals.runs.create(eval_id=eval_object.id, name="workshop run", data_source=data_source)
print("🚀 Run:", run.id, "-", run.status)

while run.status not in ("completed", "failed"):
    time.sleep(6)
    run = openai_client.evals.runs.retrieve(run_id=run.id, eval_id=eval_object.id)
    print("   status:", run.status)

print("\\nResult counts:", run.result_counts)
print("🔗 Report:", run.report_url)
'''),
    md("""
### Read the per-item scores

Each output item carries the evaluator results. A **mixed pass/fail result is
normal and is exactly the point** — evaluation surfaces the questions where the
copilot grounds weakly or drifts, so you can fix instructions or data before
shipping. The interactive **Report URL** above shows each score and the model's
reasoning.
"""),
    code('''
if run.status == "completed":
    items = list(openai_client.evals.runs.output_items.list(run_id=run.id, eval_id=eval_object.id))
    print(f"{len(items)} items graded. Passed {run.result_counts.passed}/{run.result_counts.total}.")
    for it in items:
        results = getattr(it, "results", None) or []
        parts = []
        for r in results:
            rd = r if isinstance(r, dict) else getattr(r, "__dict__", {})
            name = rd.get("name") or rd.get("metric")
            passed = rd.get("passed")
            if name is not None:
                parts.append(f"{name}={passed}")
        print("  •", ", ".join(parts) if parts else "(open the Report URL for details)")
    print("\\nOpen the Report URL above for the full interactive breakdown.")
else:
    print("Run did not complete — check the report URL.")
'''),
    md("""
## 🙌 Your turn

1. Add a **`builtin.task_adherence`** evaluator and re-run. Note it maps
   `{{sample.output_items}}` (the full tool-call trace) rather than the text —
   compare how strictly it grades a tool-using agent.
2. Add an **adversarial / out-of-scope** query (the dataset's `qa-12` asks about
   Abraham Lincoln) and confirm the copilot declines — a safety behaviour you'd
   gate on.
3. Turn this into a **quality gate**: assert `result_counts.passed == total` and
   raise if not — the seed of a CI check.
"""),
    code('''
# 👉 Your experiment here.
'''),
    md("""
## Clean up
"""),
    code('''
config.delete_agent(project_client, eval_agent)
openai_client.evals.delete(eval_id=eval_object.id)
print("🗑️  Deleted eval agent and evaluation.")
'''),
    md("""
## 🎓 Workshop complete

You built a **Schneider Field Service Technician Copilot** end to end:

| Lab | Capability |
|---|---|
| 00-01 | Foundry connectivity + a persona-driven agent |
| 02 | Function tools (installed base, warranty, escalation) |
| 03 | File Search grounding on product manuals |
| 04 | Enterprise grounding with Azure AI Search |
| 05 | One copilot orchestrating all capabilities |
| 06 | Observability + evaluation for trust |
| 07 | Content Understanding — clean data into the RAG pipeline |
| 08 | Guardrails — Prompt Shields, PII & a custom blocklist |
| 09 | Red teaming — measure how well the defences hold |

**Continue to [Lab 07 · Content Understanding](07-document-extraction.ipynb)** to fix
the *front* of the RAG pipeline, then the two Trust & Safety capstones (08, 09).

**Next steps:** deploy as a hosted agent (`hosted-agents/`), wire evals into
CI/CD (`AgentOps/`), and replace the synthetic manuals with your real, governed
knowledge base.
"""),
]

if __name__ == "__main__":
    path = save(cells, "06-observability-and-evaluation.ipynb")
    print("Wrote", path)
