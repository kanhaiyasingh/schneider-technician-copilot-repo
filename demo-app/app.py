"""Schneider Field Service Copilot — showcase app.

A polished, end-user-facing Streamlit app that demos the full workshop arc before
participants build it themselves in the notebooks:

    Copilot · Agent · Tools · File Search · AI Search (RAG) · Observability · Evaluation

Run this app with the workshop's OWN virtual environment, e.g. (from this folder):

    ..\\.venv\\Scripts\\python.exe -m streamlit run app.py   (Windows)
    ../.venv/bin/python -m streamlit run app.py                (macOS/Linux)

with .env configured + `az login`. Launching via a bare `streamlit run app.py`
picks up whatever `streamlit` is first on PATH, which may be a different
environment that is missing the workshop dependencies.
"""
from __future__ import annotations

import base64
import importlib.util
import shutil
import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

HERE = Path(__file__).resolve().parent
GREEN = "#3DCD58"

st.set_page_config(
    page_title="Schneider Field Service Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Preflight: fail fast (and clearly) if launched from the wrong environment
# =============================================================================
def _preflight() -> None:
    """Verify the interpreter running Streamlit has the workshop deps.

    A bare ``streamlit run app.py`` uses whatever ``streamlit`` is first on
    PATH, which may be a different environment missing ``agent_framework_foundry``
    etc. Rather than a confusing traceback mid-demo, show the exact fix.
    """
    required = ("agent_framework", "agent_framework_foundry", "azure.ai.projects")
    missing = [m for m in required if importlib.util.find_spec(m) is None]
    if not missing:
        return

    repo_root = HERE.parents[0]  # demo-app -> repo root (where .venv lives)
    if sys.platform.startswith("win"):
        launch = r"..\.venv\Scripts\python.exe -m streamlit run app.py"
    else:
        launch = "../.venv/bin/python -m streamlit run app.py"

    st.error(
        "**This app is running in the wrong Python environment.**\n\n"
        f"Missing package(s): `{', '.join(missing)}`\n\n"
        f"Streamlit is running under:\n\n`{sys.executable}`\n\n"
        "Launch it instead with the workshop's own virtual environment "
        f"(`{repo_root / '.venv'}`). From this `demo-app/` folder, run:\n\n"
        f"```\n{launch}\n```\n\n"
        "If that venv is missing the deps, install them first with:\n\n"
        "```\npip install -r ../requirements.txt\npip install -r requirements.txt\n```"
    )
    st.stop()


_preflight()

import copilot_backend as be  # noqa: E402  (after preflight so the error is friendly)


# =============================================================================
# Styling
# =============================================================================
def _logo_data_uri() -> str:
    svg = (HERE / "assets" / "logo.svg").read_text(encoding="utf-8")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


st.markdown(
    f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');
      #MainMenu, footer {{visibility: hidden;}}
      /* Let the app's hero show through instead of Streamlit's opaque top bar,
         and push content below the floating toolbar so nothing is clipped. */
      header[data-testid="stHeader"] {{background: transparent;}}
      div[data-testid="stToolbar"] {{right: 1rem;}}
      .block-container {{padding-top: 4.75rem; max-width: 1240px;}}
      .se-header {{
        position: relative; overflow: hidden;
        display:flex; align-items:center; gap:36px;
        background:
          radial-gradient(1100px 320px at 12% -50%, rgba(61,205,88,.30), transparent 60%),
          linear-gradient(105deg, #0b0f14 0%, #10261a 52%, #17512b 100%);
        border-radius: 20px; padding: 48px 56px; margin: 0 0 24px 0;
        min-height: 300px;
        border: 1px solid rgba(61,205,88,.30);
        box-shadow: 0 12px 44px rgba(0,0,0,.38);
      }}
      .se-header::after {{
        content:""; position:absolute; right:-70px; top:-70px;
        width:340px; height:340px; border-radius:50%;
        background: radial-gradient(circle, rgba(61,205,88,.16), transparent 70%);
        pointer-events:none;
      }}
      .se-header .se-logo {{
        width:168px; height:168px; flex-shrink:0;
        background-image:url("{_logo_data_uri()}");
        background-repeat:no-repeat; background-position:center; background-size:contain;
        filter: drop-shadow(0 8px 20px rgba(0,0,0,.5));
      }}
      /* .se-header prefix + !important beat Streamlit's stMarkdownContainer p rule */
      .se-header .se-eyebrow {{
        font-family:'Inter','Segoe UI',system-ui,sans-serif !important;
        color:{GREEN} !important; font-size:1.2rem !important; font-weight:700 !important;
        text-transform:uppercase; letter-spacing:.14em !important;
        margin:0 0 6px 0 !important; line-height:1.1 !important;
      }}
      .se-header .se-title {{
        font-family:'Poppins','Segoe UI',system-ui,-apple-system,sans-serif !important;
        color:#fff !important; font-size:2.9rem !important; font-weight:600 !important;
        line-height:1.08 !important; margin:0 !important; letter-spacing:-.4px !important;
      }}
      .se-header .se-sub {{
        font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif !important;
        color:#cbd5dc !important; font-size:1.3rem !important; font-weight:400 !important;
        margin:16px 0 0 0 !important; max-width:720px; line-height:1.45 !important;
      }}
      .se-badge {{
        position:absolute; top:24px; right:28px;
        font-family:'Inter','Segoe UI',system-ui,sans-serif;
        background:rgba(255,255,255,.10); color:#e6edf3;
        border:1px solid rgba(255,255,255,.20); border-radius:999px;
        padding:9px 18px; font-size:1rem; font-weight:600; white-space:nowrap;
        backdrop-filter: blur(4px);
      }}
      .stTabs [data-baseweb="tab-list"] {{gap: 2px; flex-wrap: wrap;}}
      .stTabs [data-baseweb="tab"] {{
        border-radius: 8px 8px 0 0; padding: 8px 14px; font-weight: 600;
      }}
      .stTabs [aria-selected="true"] {{
        background: rgba(61,205,88,.14); border-bottom: 2px solid {GREEN};
      }}
      div.stButton > button {{border-radius: 8px; font-weight: 600;}}
      div.stButton > button:hover {{border-color: {GREEN}; color: {GREEN};}}
      .se-cap {{
        background: rgba(61,205,88,.07); border-left: 3px solid {GREEN};
        border-radius: 6px; padding: 10px 14px; font-size:.9rem; margin-bottom: 10px;
      }}
      .se-disclaimer {{color:#8b949e; font-size:.75rem; margin-top:8px;}}
    </style>

    <div class="se-header">
      <div class="se-logo" role="img" aria-label="Field Service Copilot logo"></div>
      <div>
        <p class="se-eyebrow">Schneider Electric</p>
        <p class="se-title">Field Service Copilot</p>
        <p class="se-sub">An AI assistant for on-site technicians — grounded in product manuals &amp; your installed base</p>
      </div>
      <span class="se-badge">🧪 Demo · Microsoft Foundry</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Sidebar
# =============================================================================
with st.sidebar:
    st.markdown("### About this demo")
    st.write(
        "This app showcases the **end product** you'll build in the workshop labs. "
        "Each tab lights up one Microsoft Foundry capability."
    )
    st.markdown(
        f"""
        | Tab | Capability | Lab |
        |---|---|---|
        | 🤖 Copilot | Full orchestration | 05 |
        | 💬 Agent | Persona agent | 01 |
        | 🛠️ Tools | Function tools | 02 |
        | 📄 File Search | Hosted RAG | 03 |
        | 🔎 AI Search | Enterprise RAG | 04 |
        | 📑 Content Understanding | Document extraction | 07 |
        | 📡 Observability | Tracing | 06 |
        | ✅ Evaluation | Quality scoring | 06 |
        | 🛡️ Guardrails | Prompt Shields, PII & blocklist | 08 |
        | 🧨 Red Teaming | Adversarial ASR scan | 09 |
        """
    )
    st.divider()
    st.markdown("**Environment**")
    st.code(f"model:  {be.config.MODEL}\nindex:  {be.config.WORKSHOP_INDEX_NAME}", language="text")
    if st.button("🔁 Reset & clean up agents", use_container_width=True,
                 help="Delete the server-side agents / vector store this app created."):
        be.cleanup()
        st.success("Cleaned up server-side resources.")
    st.markdown(
        "<p class='se-disclaimer'>⚠️ All data (manuals, serials, fault codes) is "
        "<b>synthetic</b> and for training only. Not affiliated with or endorsed "
        "by Schneider Electric. Requires <code>az login</code> + a configured "
        "<code>.env</code>.</p>",
        unsafe_allow_html=True,
    )


# =============================================================================
# Helpers
# =============================================================================
def capability_note(text: str) -> None:
    st.markdown(f"<div class='se-cap'>{text}</div>", unsafe_allow_html=True)


def question_box(key: str, samples: list[str], height_label: str = "Ask the copilot") -> str:
    """Render sample-question buttons + a text area. Returns current question text."""
    state_key = f"q_{key}"
    st.session_state.setdefault(state_key, samples[0] if samples else "")
    st.caption("Try a sample question:")
    cols = st.columns(len(samples)) if samples else []
    for i, s in enumerate(samples):
        short = (s[:42] + "…") if len(s) > 43 else s
        if cols[i].button(short, key=f"btn_{key}_{i}", help=s, use_container_width=True):
            st.session_state[state_key] = s
    return st.text_area(height_label, key=state_key, height=90)


def render_answer(res: dict) -> None:
    if res.get("ok"):
        st.markdown(res["answer"])
    else:
        st.error(res.get("answer") or res.get("error") or "Something went wrong.")


TOOL_LABELS = {
    "lookup_asset_by_serial": "🔧 Asset lookup",
    "list_assets_for_site": "📍 Site inventory",
    "check_warranty_and_contract": "📋 Warranty / contract",
    "search_product_manuals": "📚 Manual search",
}


def render_tools(res: dict) -> None:
    tools = res.get("tools") or []
    if not tools:
        st.caption("_No tools were called for this question._")
        return
    st.markdown("**🧰 Tool activity** — what the agent decided to call:")
    for t in tools:
        label = TOOL_LABELS.get(t["tool"], t["tool"])
        st.markdown(f"- {label} · `{t['tool']}(` `{t['input']}` `)`")


def render_pdf(path: Path) -> None:
    """Preview the source document.

    Edge/Chrome block PDFs embedded in iframes (data: URIs and nested component
    iframes both get blocked). So we prefer a rendered PNG of the report — an
    ordinary image is never blocked — and only fall back to the served PDF in a
    single top-level iframe if the image is missing.
    """
    preview = path.with_suffix(".png")
    if preview.exists():
        st.image(str(preview), use_container_width=True)
        return

    static_dir = HERE / "static"
    static_dir.mkdir(exist_ok=True)
    dest = static_dir / path.name
    try:
        if not dest.exists() or dest.stat().st_mtime < path.stat().st_mtime:
            shutil.copyfile(path, dest)
    except OSError:
        pass
    url = f"app/static/{quote(path.name)}"
    components.iframe(url, height=520, scrolling=True)
    st.markdown(
        f'<a href="{url}" target="_blank" rel="noopener" '
        'style="color:#3DCD58;font-size:0.88rem;">'
        'Preview blank or blocked? Open the PDF in a new tab ↗</a>',
        unsafe_allow_html=True,
    )


# =============================================================================
# Tabs
# =============================================================================
tab_copilot, tab_agent, tab_tools, tab_fs, tab_ai, tab_cu, tab_obs, tab_eval, tab_guard, tab_red = st.tabs(
    ["🤖 Copilot", "💬 Agent", "🛠️ Tools", "📄 File Search",
     "🔎 AI Search", "📑 Content Understanding", "📡 Observability", "✅ Evaluation",
     "🛡️ Guardrails", "🧨 Red Teaming"]
)

# --- 🤖 Complete Copilot ------------------------------------------------------
with tab_copilot:
    st.subheader("The complete field copilot")
    capability_note(
        "One agent, <b>all</b> the tools. It looks up the installed base "
        "(warranty, site, escalation) <i>and</i> searches the product manuals, "
        "then merges everything into one safety-first, cited answer. This is the "
        "end product participants build in Lab 05."
    )
    q = question_box("copilot", be.SAMPLE_QUESTIONS["copilot"])
    if st.button("Ask the copilot ⚡", key="run_copilot", type="primary"):
        with st.spinner("Thinking — calling tools and searching manuals…"):
            res = be.run_copilot(q)
        render_answer(res)
        st.divider()
        render_tools(res)

# --- 💬 Agent -----------------------------------------------------------------
with tab_agent:
    st.subheader("A persona agent (no grounding yet)")
    capability_note(
        "The simplest building block: a model + a <b>persona</b> (safety-first "
        "field technician). Great tone — but with no tools or manuals it can "
        "<b>hallucinate</b> a fault-code meaning. That gap motivates every tab "
        "that follows. (Lab 01)"
    )
    q = question_box("agent", be.SAMPLE_QUESTIONS["agent"])
    if st.button("Ask the agent", key="run_agent", type="primary"):
        with st.spinner("Asking the persona agent…"):
            res = be.run_agent(q)
        render_answer(res)
        st.info("💡 Ask it about a specific fault code and watch it guess — then "
                "compare with the **File Search** and **AI Search** tabs.")

# --- 🛠️ Tools -----------------------------------------------------------------
with tab_tools:
    st.subheader("Function tools — live installed-base lookups")
    capability_note(
        "Now the agent can <b>act</b>. It calls Python functions to look up an "
        "asset by serial, list a site's equipment, and check "
        "warranty/contract — flagging cases that need <b>escalation</b>. Watch the "
        "tool-activity panel below. (Lab 02)"
    )
    q = question_box("tools", be.SAMPLE_QUESTIONS["tools"])
    if st.button("Run with tools", key="run_tools", type="primary"):
        with st.spinner("Calling installed-base tools…"):
            res = be.run_tools(q)
        render_answer(res)
        st.divider()
        render_tools(res)

# --- 📄 File Search -----------------------------------------------------------
with tab_fs:
    st.subheader("File Search — grounded on the product manuals")
    capability_note(
        "Upload the manuals into a hosted <b>vector store</b> and the agent "
        "retrieves the real text and <b>cites</b> it — no more guessing. First "
        "run uploads the manuals (a few seconds). (Lab 03)"
    )
    q = question_box("file_search", be.SAMPLE_QUESTIONS["file_search"])
    if st.button("Search the manuals", key="run_fs", type="primary"):
        with st.spinner("Uploading manuals (first time) and searching…"):
            res = be.run_file_search(q)
        render_answer(res)
        st.caption("Citations like 【4:0†source】 point back to the manual chunk used.")

# --- 🔎 AI Search -------------------------------------------------------------
with tab_ai:
    st.subheader("Azure AI Search — enterprise RAG")
    capability_note(
        "Production-grade grounding: a <b>vector + semantic</b> index over the "
        "manuals, queried through the project's Azure AI Search connection. Same "
        "cited answers, enterprise scale & governance. (Lab 04)"
    )
    if st.button("① Check / build the search index", key="build_idx"):
        with st.spinner("Ensuring the index exists and is populated…"):
            status = be.ensure_ai_search_ready()
        if status.get("ok"):
            msg = f"Index **{status['index']}** ready · {status['doc_count']} chunks"
            st.success(msg + (" (just built)" if status.get("built") else " (already existed)"))
        else:
            st.error(status.get("error", "Could not prepare the index."))
    q = question_box("ai_search", be.SAMPLE_QUESTIONS["ai_search"])
    if st.button("Search with Azure AI Search", key="run_ai", type="primary"):
        with st.spinner("Running semantic search + grounded answer…"):
            res = be.run_ai_search(q)
        render_answer(res)

# --- 📑 Content Understanding -------------------------------------------------
with tab_cu:
    st.subheader("Content Understanding — extract clean data from complex PDFs")
    capability_note(
        "Before RAG can work, messy source documents must become clean, structured "
        "text. <b>Azure AI Content Understanding</b> turns a complex field-service "
        "PDF — multi-column tables, a fault-code matrix, torque specs, a wiring "
        "diagram — into RAG-ready <b>Markdown</b> <i>and</i> <b>structured fields</b>. "
        "We then ground the copilot on that extracted index. This fixes the "
        "<b>front</b> of the RAG pipeline. (Lab 07)"
    )

    st.markdown("#### ① The source document")
    st.caption("A real-world-style field-service report: tables, a fault-code matrix, "
               "measured readings, and a wiring diagram.")
    pdf_path = be.cu_pdf_path()
    if pdf_path.exists():
        render_pdf(pdf_path)
        st.download_button("⬇️ Download the PDF", data=pdf_path.read_bytes(),
                           file_name=pdf_path.name, mime="application/pdf")
    else:
        st.warning(f"Complex PDF not found at `{pdf_path}`. Generate it with "
                   "`python src/gen_complex_doc.py`.")

    st.divider()
    st.markdown("#### ② What Content Understanding extracts")
    if st.button("Extract with Content Understanding ✨", key="run_cu", type="primary"):
        with st.spinner("Analyzing the PDF with Content Understanding "
                        "(Markdown + structured fields)…"):
            st.session_state["cu_ext"] = be.run_cu_extract()
    ext = st.session_state.get("cu_ext")
    if ext and ext.get("ok"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Naive text dump", f"{ext['naive_chars']:,} chars")
        c2.metric("CU clean Markdown", f"{ext['cu_chars']:,} chars")
        c3.metric("Tables recovered", ext["tables"])
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**❌ Naive PDF text dump** — what basic ingestion sees")
            st.code(ext["naive_text"][:2500] or "(no extractable text)", language="text")
        with col_r:
            st.markdown("**✅ Content Understanding Markdown** — tables preserved")
            st.code(ext["markdown"][:2500], language="markdown")
        fields = ext.get("fields") or {}
        if fields:
            st.markdown("**🔑 Structured fields** — pulled by a custom analyzer")
            meta = {k: v for k, v in fields.items() if k != "FaultCodes"}
            st.json(meta)
            fault_codes = fields.get("FaultCodes") or []
            if fault_codes:
                import pandas as pd

                st.markdown("**Fault-code matrix, extracted as structured rows:**")
                st.dataframe(pd.DataFrame(fault_codes),
                             use_container_width=True, hide_index=True)
    elif ext:
        st.error(ext.get("error") or "Extraction failed.")

    st.divider()
    st.markdown("#### ③ Ask questions grounded on the extracted data")
    capability_note(
        "The clean chunks are indexed into <b>schneider-extracted-index</b>. Ask a "
        "question whose answer lives only in the PDF's tables — the copilot "
        "retrieves it from the extracted index and answers, grounded and cited."
    )
    if st.button("① Extract & build the index", key="build_ext_idx"):
        with st.spinner("Extracting (if needed) and building the index…"):
            status = be.ensure_extracted_index_ready()
        if status.get("ok"):
            st.success(f"Index **{status['index']}** ready · {status['doc_count']} chunks"
                       + (" (just built)" if status.get("built") else " (already existed)"))
        else:
            st.error(status.get("error", "Could not prepare the index."))
    q = question_box("content_understanding", be.SAMPLE_QUESTIONS["content_understanding"])
    if st.button("Ask the extracted knowledge", key="run_cu_search", type="primary"):
        with st.spinner("Searching the extracted index and answering…"):
            res = be.run_extracted_search(q)
        render_answer(res)


# --- 📡 Observability ---------------------------------------------------------
with tab_obs:
    st.subheader("Observability — every answer is traced")
    capability_note(
        "Trustworthy AI needs an audit trail. Each query runs inside an "
        "OpenTelemetry <b>span</b> (site, category, latency, tool calls) exported "
        "to <b>Application Insights</b>. Use the Trace ID to find it in the "
        "Foundry portal → Tracing. (Lab 06)"
    )
    q = question_box("observability", be.SAMPLE_QUESTIONS["observability"])
    if st.button("Ask (traced)", key="run_obs", type="primary"):
        with st.spinner("Answering and emitting a trace…"):
            res = be.run_traced(q)
        render_answer(res)
        if res.get("trace_id"):
            st.success(f"📡 Emitted trace — **Trace ID:** `{res['trace_id']}`")
            st.caption("Find it in Foundry portal → **Tracing**, or Application "
                       "Insights → **Transaction search** (role "
                       "`schneider-technician-copilot`). Allow 1–3 minutes to appear.")

# --- ✅ Evaluation ------------------------------------------------------------
with tab_eval:
    st.subheader("Evaluation — score answer quality")
    capability_note(
        "Before shipping, grade the copilot with Foundry's server-side "
        "evaluators — <b>relevance</b>, <b>coherence</b>, <b>fluency</b> — over a "
        "set of questions. A mixed pass/fail result is the point: it surfaces "
        "weak answers before the field does. (Lab 06)"
    )
    default_qs = "\n".join(be.SAMPLE_QUESTIONS["evaluation"])
    qs_text = st.text_area("Questions to evaluate (one per line):", value=default_qs, height=110)
    st.caption("⏱️ A run takes ~1–2 minutes (each question is answered, then graded).")
    if st.button("Run evaluation", key="run_eval", type="primary"):
        questions = [l.strip() for l in qs_text.splitlines() if l.strip()]
        with st.spinner(f"Evaluating {len(questions)} questions…"):
            res = be.run_evaluation(questions)
        if res.get("ok"):
            passed, total = res.get("passed"), res.get("total")
            st.success(f"✅ Completed — **{passed}/{total}** metric checks passed")
            rows = res.get("rows") or []
            if rows:
                import pandas as pd

                table = []
                for i, m in enumerate(rows):
                    row = {"#": i + 1}
                    row.update({k: ("✅" if v else "❌") for k, v in m.items()})
                    table.append(row)
                st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
            if res.get("report_url"):
                st.markdown(f"🔗 [Open the full interactive report]({res['report_url']})")
        else:
            st.error(res.get("error") or f"Evaluation status: {res.get('status')}")

# --- 🛡️ Guardrails -----------------------------------------------------------
with tab_guard:
    st.subheader("Guardrails — Prompt Shields, PII & a custom blocklist")
    capability_note(
        "A helpful copilot is also a <b>target</b>: technicians try to jailbreak it, "
        "paste customer <b>PII</b>, or coax it into discussing <b>competitors</b> and "
        "internal <b>codenames</b>. We stack <b>three layered guardrails</b> on a "
        "guardrailed model deployment using the real Azure <b>Content Safety</b> RAI "
        "surface — enforced by the <b>platform</b>, not a system prompt the model can "
        "be argued out of. (Lab 08)"
    )

    st.markdown("#### ① Provision the guardrailed copilot")
    st.caption("Creates a blocklist (PII regex + synthetic competitor/codename terms), "
               "an RAI policy with Prompt Shields, a small guardrailed deployment, and "
               "pins an agent to it. Idempotent — reused on later runs.")
    if st.button("Provision guardrails 🛡️", key="guard_provision", type="primary"):
        with st.spinner("Provisioning blocklist, RAI policy, deployment + agent "
                        "(first run can take a few minutes)…"):
            st.session_state["guard_ready"] = be.ensure_guardrails_ready()
    ready = st.session_state.get("guard_ready")
    if ready and ready.get("ok"):
        st.success(f"Guardrailed deployment **{ready['deployment']}** — "
                   f"{ready['state']} · {ready['entries']} blocklist entries"
                   + (" (just provisioned)" if ready.get("built") else " (reused)"))
        for layer in ready.get("layers", []):
            st.markdown(f"- {layer}")
    elif ready:
        st.error(ready.get("error") or "Could not provision guardrails.")

    st.divider()
    st.markdown("#### ② Send a prompt through the guardrails")
    capability_note(
        "A <b>benign</b> field question passes; an <b>attack</b> is stopped at the "
        "gate and the verdict names <b>which layer</b> fired. Provision first (①)."
    )
    st.session_state.setdefault("guard_prompt", be.GUARDRAIL_PROMPTS[0]["prompt"])
    st.caption("Try a sample prompt:")
    gcols = st.columns(len(be.GUARDRAIL_PROMPTS))
    for i, p in enumerate(be.GUARDRAIL_PROMPTS):
        icon = "✅" if p["kind"] == "benign" else "🛑"
        if gcols[i].button(f"{icon} {p['label']}", key=f"guard_btn_{i}",
                           help=p["prompt"], use_container_width=True):
            st.session_state["guard_prompt"] = p["prompt"]
    prompt = st.text_area("Prompt to test", key="guard_prompt", height=90)
    if st.button("Send through the guardrails", key="guard_run", type="primary"):
        if not st.session_state.get("guard_ready", {}).get("ok"):
            st.warning("Provision the guardrails first (step ① above).")
        else:
            with st.spinner("Invoking the guardrailed agent…"):
                res = be.run_guardrail_check(prompt)
            status = res.get("status")
            if status == "answered":
                st.success("✅ Passed the guardrails — answered")
                st.markdown(res.get("answer") or "")
            elif status == "blocked":
                st.error(f"🛑 Blocked by **{res.get('layer')}**")
                if res.get("answer"):
                    st.caption(res["answer"][:300])
            elif status == "error":
                st.error(res.get("error") or "Guardrails not ready.")
            else:
                st.warning(f"⏳ Inconclusive — {res.get('layer')}: {res.get('answer')}")

# --- 🧨 Red Teaming -----------------------------------------------------------
with tab_red:
    st.subheader("Red Teaming — measure how well the defences hold")
    capability_note(
        "Guardrails are defence; red teaming is <b>offence</b>. The Azure <b>AI Red "
        "Teaming Agent</b> (PyRIT-backed) auto-generates adversarial prompts per risk "
        "category, fires them at a target, scores every response, and returns an "
        "<b>Attack Success Rate (ASR)</b> scorecard — <b>lower is better</b>. (Lab 09)"
    )
    c1, c2 = st.columns(2)
    with c1:
        target_label = st.radio(
            "Target to attack",
            ["Bare model (baseline)", "Grounded Schneider persona"],
            key="red_target",
            help="Compare the raw model against the safety-first technician persona.",
        )
    with c2:
        num_obj = st.slider("Attack prompts per category", 1, 5, 3, key="red_numobj")
    cats = st.multiselect(
        "Risk categories", list(be.REDTEAM_CATEGORIES.keys()),
        default=["Violence", "Hate/Unfairness"], key="red_cats",
    )
    st.caption("⏱️ A scan drives many model calls and logs to the Foundry portal — "
               "keep categories and objectives small for a live demo (a run takes a "
               "few minutes).")
    if st.button("Run red-team scan", key="red_run", type="primary"):
        if not cats:
            st.warning("Pick at least one risk category.")
        else:
            target = "grounded" if target_label.startswith("Grounded") else "model"
            with st.spinner(f"Scanning {len(cats)} categories × {num_obj} objectives "
                            "(this can take a few minutes)…"):
                res = be.run_redteam_scan(target=target, categories=cats, num_objectives=num_obj)
            if res.get("ok"):
                st.success(f"✅ Scan complete — **{res['scan_name']}**")
                st.metric("Overall ASR (lower is better)",
                          f"{res['overall_asr']:.1f}%",
                          help=f"{res['overall_success']}/{res['overall_total']} attacks succeeded")
                rows = res.get("rows") or []
                if rows:
                    import pandas as pd

                    df = pd.DataFrame([{
                        "Risk category": r["category"],
                        "ASR": f"{r['asr']:.1f}%",
                        "Successful": r["success"],
                        "Total": r["total"],
                    } for r in rows])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption("Any non-zero category is a prioritised gap — tighten the "
                           "Guardrails (tab ←) and re-scan to confirm ASR drops. Drill "
                           "into individual attack/response pairs in Foundry portal → "
                           "Red teaming.")
            else:
                if res.get("needs_install"):
                    st.warning("🧩 " + (res.get("error") or "PyRIT dependency missing."))
                    st.caption("Install the red-teaming extra from the `demo-app` "
                               "folder, then restart the app:")
                    st.code(res.get("install_cmd", ""), language="powershell")
                else:
                    st.error(res.get("error") or "Red-team scan failed.")

st.markdown(
    "<p class='se-disclaimer'>Built for the Schneider Electric × Microsoft Foundry "
    "bootcamp · synthetic data · keyless (Entra ID) auth.</p>",
    unsafe_allow_html=True,
)
