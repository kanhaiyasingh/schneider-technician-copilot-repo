"""Builder for Lab 09 — Trust: Red-Teaming the copilot with the AI Red Teaming Agent.

Lab 09 is the offensive half of Trust & Safety. In Lab 08 you built defences —
here you *measure* whether they hold. The Azure **AI Red Teaming Agent**
(`azure-ai-evaluation[redteam]`, PyRIT-backed) auto-generates adversarial prompts
across risk categories, fires them at a target, scores every response, and hands
you an **Attack Success Rate (ASR)** scorecard.

Flow: a basic scan on the bare model → an advanced scan with encoding strategies +
languages → read the scorecard → (Your turn) point the same scan at the grounded
Schneider copilot and compare.

Ported from foundry-workshop `12-red-teaming`, re-themed to Schneider.
"""
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
# Lab 09 · Trust — Red-Teaming the copilot

In [Lab 08](08-guardrails.ipynb) you *built* defences. How do you know they
**hold**? You **red team**: automatically generate adversarial prompts, fire them
at your system, and measure how often it produces harmful content. The **AI Red
Teaming Agent** wraps Microsoft's open-source **PyRIT** toolkit — it seeds attack
objectives per risk category, optionally mutates them with evasion **strategies**,
scores every response, and gives you a scorecard.

```
RedTeam  ──seeds objectives──▶  your target callback  ──▶  model / agent
   │                                                            │
   │◀── PyRIT scorer (pass/fail per attack) ──── responses ─────┘
   ▼
Attack Success Rate (ASR) scorecard   ◀── lower is better
```

> 🧭 **Prerequisites:**
> - `pip install "azure-ai-evaluation[redteam]"` (already in `requirements.txt`).
> - A **supported region** for the Red Teaming Agent — e.g. **East US 2**, **Sweden
>   Central**, **France Central**, **Switzerland West**.
> - **Python 3.10–3.13** (PyRIT excludes 3.9 and 3.14+).
> - **Azure AI User** on the project (the scan logs results there).

> ⚠️ Synthetic training data — not affiliated with or endorsed by Schneider Electric.
"""),
    md("""
## 1. Configure

Same `.env` as every lab. The Red Teaming Agent needs your **project endpoint** (it
logs the scan there) and a model to attack. We check the Python version up front,
because an unsupported kernel is the most common failure here.
"""),
    code(BOOTSTRAP + '''
import sys as _sys

assert (3, 10) <= _sys.version_info < (3, 14), (
    f"PyRIT requires Python 3.10-3.13; current is {_sys.version.split()[0]}. "
    "Switch to the 'Python (FoundryLabs .venv)' kernel."
)

PROJECT_ENDPOINT = config.PROJECT_ENDPOINT
CHAT_MODEL       = config.MODEL

print("Project :", PROJECT_ENDPOINT)
print("Model   :", CHAT_MODEL)
print("Python  :", _sys.version.split()[0], "(OK)")
'''),
    md("""
!!! note "Expected output"
    ```
    Project : https://<resource>.services.ai.azure.com/api/projects/<project>
    Model   : gpt-5.4
    Python  : 3.12.x (OK)
    ```
    An `AssertionError` means your kernel is on an unsupported Python — switch to a
    3.10-3.13 kernel before continuing.
"""),
    md("""
## 2. The target callback

The scanner needs a **target** to attack: a callable that takes a prompt string and
returns the model's reply. We start by attacking the **bare chat model** directly —
*no persona, no grounding, no guardrails* — to establish a baseline. In sections 6+
and the "Your turn" you'll repoint this callback at the **grounded, guardrailed
copilot** and watch the numbers move.
"""),
    code('''
credential     = config.get_credential()
project_client = config.get_project_client()
openai_client  = project_client.get_openai_client()

def target_callback(query: str) -> str:
    """System under test #1: the bare chat model (no persona / grounding)."""
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": query}],
    )
    return response.choices[0].message.content

# Smoke-test the target before handing it to the scanner.
print("smoke test:", target_callback("Say hello in one word."))
'''),
    md("""
!!! note "Expected output"
    ```
    smoke test: Hello!
    ```
    A normal reply means the scanner can drive the target. The callback contract is
    just *string in, string out* — so it can wrap anything you own (a bare model, an
    agent, a full RAG app).
"""),
    md("""
## 3. Build the Red Team agent

`RedTeam` is the scanner. You give it the **project** (where results are logged), a
**credential**, the **risk categories** to probe, and `num_objectives` — how many
distinct attack prompts to generate *per category*. Four categories × 5 objectives
= 20 baseline prompts, enough to see the shape without a long run.
"""),
    code('''
from azure.ai.evaluation.red_team import RedTeam, RiskCategory

red_team = RedTeam(
    azure_ai_project=PROJECT_ENDPOINT,
    credential=credential,
    risk_categories=[
        RiskCategory.Violence,
        RiskCategory.HateUnfairness,
        RiskCategory.Sexual,
        RiskCategory.SelfHarm,
    ],
    num_objectives=5,   # attack prompts per category
)
print("RedTeam ready — 4 categories × 5 objectives = 20 baseline prompts")
'''),
    md("""
!!! note "Expected output"
    ```
    RedTeam ready — 4 categories × 5 objectives = 20 baseline prompts
    ```
    Start small: `num_objectives=5` keeps the run inside the lab budget. Crank it up
    once you're scanning for real.
"""),
    md("""
## 4. Run the basic scan

`scan(...)` is **async** — top-level `await` works in a notebook kernel. It seeds
the baseline objectives, drives them through your `target_callback`, scores each
response with PyRIT, and writes results to `output_path`. A 20-prompt scan takes a
few minutes.

!!! note "Windows console noise"
    On Windows you may see occasional `UnicodeEncodeError` **logging** tracebacks
    (PyRIT debug-logs emoji through a cp1252 console). These are harmless — the scan
    still completes and the scorecard is written.
"""),
    code('''
basic_result = await red_team.scan(
    target=target_callback,
    scan_name="schneider-redteam-basic",
    output_path="redteam_basic_output",
)
print("✅ basic scan complete — results in redteam_basic_output/")
'''),
    md("""
!!! note "Expected output"
    ```
    ✅ basic scan complete — results in redteam_basic_output/
    ```
    The folder holds `results.json` (every attack/response pair) and
    `evaluation_results.json` (the aggregated scorecard on disk). We read the same
    scorecard straight off the returned object with `.to_scorecard()` next.

!!! tip "In a plain script, not a notebook?"
    Top-level `await` needs an IPython kernel. In a `.py` file, wrap the call:
    `asyncio.run(red_team.scan(...))`.
"""),
    md("""
## 5. Read the ASR scorecard

The headline metric is **Attack Success Rate (ASR)**: the fraction of adversarial
prompts that *succeeded* in eliciting harmful content. **Lower is better.** The
scorecard breaks ASR down by risk category — so you see exactly where the model is
weakest.
"""),
    code('''
# scan() returns a RedTeamResult; .to_scorecard() gives the version-correct dict.
scorecard = basic_result.to_scorecard() or {}
risk      = (scorecard.get("risk_category_summary") or [{}])[0]

print(f"{'category':<18}{'ASR':>8}{'success':>9}{'total':>7}")
print("-" * 42)
print(f"{'OVERALL':<18}{risk.get('overall_asr', 0):>7.1f}%"
      f"{risk.get('overall_successful_attacks', 0):>9}{risk.get('overall_total', 0):>7}")
for cat, key in [("Violence", "violence"), ("Hate/Unfairness", "hate_unfairness"),
                 ("Sexual", "sexual"), ("Self-Harm", "self_harm")]:
    print(f"{cat:<18}{risk.get(key + '_asr', 0):>7.1f}%"
          f"{risk.get(key + '_successful_attacks', 0):>9}{risk.get(key + '_total', 0):>7}")
'''),
    md("""
!!! note "Expected output"
    ```
    category               ASR  success  total
    ------------------------------------------
    OVERALL              10.0%        2     20
    Violence             20.0%        1      5
    Hate/Unfairness       0.0%        0      5
    Sexual               20.0%        1      5
    Self-Harm             0.0%        0      5
    ```
    Exact numbers vary per run. Any non-zero category is your prioritised to-do list —
    tighten it (the [Lab 08](08-guardrails.ipynb) filters are one lever) and re-scan
    to confirm the number drops.
"""),
    md("""
## 6. Advanced — evasion strategies + languages

Baseline prompts are the easy case. Real attackers **obfuscate** (Base64, ROT13,
Unicode confusables) and probe in **other languages**. `attack_strategies` mutates
each objective through these encodings — a **nested list** element chains two
strategies together (Base64-then-ROT13). Non-English probing is set once on the
`RedTeam` via the `language` argument. This is the scan that finds the leaks a
baseline misses. We narrow to two categories to keep the run in budget.
"""),
    code('''
from azure.ai.evaluation.red_team import AttackStrategy, SupportedLanguages

advanced = RedTeam(
    azure_ai_project=PROJECT_ENDPOINT,
    credential=credential,
    risk_categories=[RiskCategory.Violence, RiskCategory.HateUnfairness],
    num_objectives=5,
    language=SupportedLanguages.Spanish,   # probe in Spanish, not English
)

advanced_result = await advanced.scan(
    target=target_callback,
    scan_name="schneider-redteam-advanced",
    attack_strategies=[
        AttackStrategy.Base64,
        AttackStrategy.ROT13,
        AttackStrategy.UnicodeConfusable,
        [AttackStrategy.Base64, AttackStrategy.ROT13],   # composed: Base64 -> ROT13
    ],
    output_path="redteam_advanced_output",
)
print("✅ advanced scan complete — encoding strategies + Spanish")
'''),
    md("""
!!! note "Expected output"
    ```
    ✅ advanced scan complete — encoding strategies + Spanish
    ```
    Each baseline objective is now fired several ways (plain, Base64, ROT13,
    confusable, and a composed Base64→ROT13) in Spanish — many more prompts than the
    basic scan, so this run takes longer.

!!! warning "API is evolving"
    `RedTeam`, `AttackStrategy`, and `SupportedLanguages` live under
    `azure.ai.evaluation.red_team` and move between releases. This lab targets the
    `azure-ai-evaluation[redteam]` version pinned in `requirements.txt` — note that
    `language` is a **single** value on the `RedTeam` constructor (not a list on
    `scan`), and strategies are **composed** by nesting a list inside
    `attack_strategies`. Check the installed version if an import or argument differs.
"""),
    md("""
## 7. Compare baseline vs. strategies

The advanced scorecard adds an **attack-technique** breakdown alongside the
risk-category one. The story to look for: an encoding strategy that scores a
*higher* ASR than baseline means that obfuscation slips past the model's defences —
a concrete gap to close before you ship.
"""),
    code('''
tech = (advanced_result.to_scorecard() or {}).get("attack_technique_summary") or [{}]
tech = tech[0]

print(f"{'technique':<14}{'ASR':>8}{'success':>9}{'total':>7}")
print("-" * 38)
for label, key in [("OVERALL", "overall"), ("baseline", "baseline"),
                   ("easy", "easy_complexity"), ("difficult", "difficult_complexity")]:
    asr = tech.get(key + "_asr")
    if asr is None:
        continue
    print(f"{label:<14}{asr:>7.1f}%"
          f"{tech.get(key + '_successful_attacks', 0):>9}{tech.get(key + '_total', 0):>7}")
'''),
    md("""
!!! note "Expected output"
    ```
    technique          ASR  success  total
    --------------------------------------
    OVERALL          16.0%        8     50
    baseline         10.0%        1     10
    easy             17.5%        7     40
    ```
    Encoded ("easy" complexity) attacks often land **more often** than baseline —
    proof that obfuscation evades defences. Every scan also logs to the **Foundry
    portal**, where you can drill into individual attack/response pairs and track ASR
    across runs.

!!! tip "This closes the safety loop"
    Guardrails ([Lab 08](08-guardrails.ipynb)) are defence; red teaming is offence;
    evaluation ([Lab 06](06-observability-and-evaluation.ipynb)) is the measuring
    tape. Run all three on every release and you have a repeatable safety pipeline.
"""),
    md("""
## 🙌 Your turn — attack the *grounded* copilot

The real question for Schneider: does the **grounded, in-scope technician persona**
resist attacks better than the bare model? Below we create a persona agent (the same
`config.TECH_PERSONA` you've used since Lab 01), wrap it in an `agent_reference`
callback, and hand *that* to the scanner. Compare its ASR to the bare-model baseline
above — a safety-first, scope-limited persona should push the number toward zero.

1. **Run the grounded scan** (cell below) and compare ASR with section 5.
2. **Add a strategy.** Append `AttackStrategy.Flip` (or `AttackStrategy.Leetspeak`)
   to the advanced `attack_strategies` and re-scan — does the new encoding raise the
   *easy*-complexity ASR?
3. **Attack the guardrailed agent.** Point the callback at the
   `schneider-tech-guarded` agent from [Lab 08](08-guardrails.ipynb) (recreate it if
   you cleaned it up) and confirm the Prompt Shields drive ASR down further.
"""),
    code('''
# Create a grounded persona agent and attack IT instead of the bare model.
persona_agent = config.create_prompt_agent(
    project_client,
    name="schneider-tech-redteam-target",
    instructions=config.TECH_PERSONA,
)

def grounded_target_callback(query: str) -> str:
    """System under test #2: the grounded, in-scope technician persona."""
    return config.ask(project_client, persona_agent, query)

print("smoke test:", grounded_target_callback("What is arc-flash PPE?")[:80], "…")

grounded_scan = RedTeam(
    azure_ai_project=PROJECT_ENDPOINT,
    credential=credential,
    risk_categories=[RiskCategory.Violence, RiskCategory.HateUnfairness],
    num_objectives=5,
)
grounded_result = await grounded_scan.scan(
    target=grounded_target_callback,
    scan_name="schneider-redteam-grounded",
    output_path="redteam_grounded_output",
)

g     = grounded_result.to_scorecard() or {}
grisk = (g.get("risk_category_summary") or [{}])[0]
print(f"\\nGrounded copilot OVERALL ASR: {grisk.get('overall_asr', 0):.1f}% "
      f"({grisk.get('overall_successful_attacks', 0)}/{grisk.get('overall_total', 0)})")
print("Compare with the bare-model baseline in section 5.")
'''),
    md("""
## Clean up
"""),
    code('''
try:
    config.delete_agent(project_client, persona_agent)
    print("🗑️  Deleted the red-team target agent.")
except Exception as exc:
    print("Cleanup warning:", str(exc)[:200])
'''),
    md("""
## 🎓 Workshop complete

You built a **Schneider Field Service Technician Copilot** end to end and made it
**trustworthy and safe**:

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

**Defence (08) + offence (09) + measurement (06) = a repeatable safety pipeline.**

**Next steps:** deploy as a hosted agent (`hosted-agents/`), wire evals + red-team
scans into CI/CD (`AgentOps/`), and replace the synthetic manuals with your real,
governed knowledge base.
"""),
]

if __name__ == "__main__":
    path = save(cells, "09-red-teaming.ipynb")
    print("Wrote", path)
