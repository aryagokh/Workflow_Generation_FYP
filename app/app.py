# import streamlit as st
# import json
# import sys
# import tempfile
# import os
# from pathlib import Path

# # ── Path fix: ensures Python can find your workflow modules ───────────────────
# # app.py must sit in the same folder as your .py workflow files.
# # If you move app.py elsewhere, update this path to point at your project root.
# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# REPO_ROOT    = os.path.dirname(PROJECT_ROOT)  # one level up — contains src/
# for p in [PROJECT_ROOT, REPO_ROOT]:
#     if p not in sys.path:
#         sys.path.insert(0, p)

# # ── Page config ───────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="CNC·AI — Workflow Generator",
#     page_icon="⚙",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # ── Custom CSS ────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
#   @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

#   html, body, [class*="css"] {
#     font-family: 'IBM Plex Sans', sans-serif;
#     background-color: #080C10;
#     color: #C8D4E0;
#   }
#   .stApp { background-color: #080C10; }
#   #MainMenu, footer, header { visibility: hidden; }
#   .block-container { padding: 2.5rem 3rem 4rem 3rem; max-width: 1280px; }

#   .top-bar {
#     display: flex; align-items: center; gap: 14px;
#     border-bottom: 1px solid #1C2A38;
#     padding-bottom: 1.4rem; margin-bottom: 2.5rem;
#   }
#   .top-bar-icon { font-size: 1.6rem; color: #3B9EFF; }
#   .top-bar-title {
#     font-family: 'IBM Plex Mono', monospace; font-size: 1.15rem;
#     font-weight: 600; letter-spacing: 0.12em; color: #EEF2F7; text-transform: uppercase;
#   }
#   .top-bar-sub {
#     font-size: 0.78rem; color: #4A6070; letter-spacing: 0.06em;
#     margin-left: auto; font-family: 'IBM Plex Mono', monospace;
#   }

#   .section-label {
#     font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
#     letter-spacing: 0.18em; text-transform: uppercase;
#     color: #3B9EFF; margin-bottom: 0.6rem; margin-top: 2rem;
#   }

#   .complexity-card {
#     border: 1px solid #1C2A38; border-radius: 6px;
#     padding: 1.2rem 1.4rem; background: #0E1620;
#   }
#   .complexity-card.active { border-color: #3B9EFF; background: #0D1E30; }
#   .card-badge {
#     display: inline-block; font-family: 'IBM Plex Mono', monospace;
#     font-size: 0.62rem; letter-spacing: 0.14em; padding: 2px 7px;
#     border-radius: 3px; margin-bottom: 0.5rem; text-transform: uppercase;
#   }
#   .badge-simple  { background: #0D2B1A; color: #3DBC78; border: 1px solid #1A5035; }
#   .badge-medium  { background: #2B1F0A; color: #E0A030; border: 1px solid #5A3A10; }
#   .badge-complex { background: #1E0B26; color: #B06EDD; border: 1px solid #4A1E6A; }
#   .card-name { font-weight: 600; font-size: 1rem; color: #EEF2F7; margin-bottom: 0.25rem; }
#   .card-method { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #4A6070; }
#   .card-desc { font-size: 0.78rem; color: #6A8090; margin-top: 0.4rem; line-height: 1.5; }

#   .rec-banner {
#     display: flex; align-items: center; gap: 10px;
#     background: #0D1E30; border: 1px solid #3B9EFF44;
#     border-left: 3px solid #3B9EFF; border-radius: 5px;
#     padding: 0.7rem 1rem; margin-bottom: 1.8rem; font-size: 0.82rem;
#   }
#   .rec-label { color: #3B9EFF; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; }
#   .rec-value { color: #EEF2F7; font-weight: 600; }

#   [data-testid="stFileUploader"] {
#     border: 1px dashed #1C2A38 !important; border-radius: 6px !important;
#     background: #0E1620 !important; padding: 0.5rem !important;
#   }

#   .stButton > button {
#     background: #3B9EFF !important; color: #000 !important;
#     font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
#     font-weight: 600 !important; letter-spacing: 0.1em !important;
#     text-transform: uppercase !important; border: none !important;
#     border-radius: 4px !important; padding: 0.6rem 2rem !important; width: 100%;
#   }
#   .stButton > button:hover { background: #5AB0FF !important; }
#   .stButton > button:disabled { background: #1C2A38 !important; color: #4A6070 !important; }

#   [data-testid="stTabs"] [data-baseweb="tab-list"] {
#     background: transparent; border-bottom: 1px solid #1C2A38; gap: 0;
#   }
#   [data-testid="stTabs"] [data-baseweb="tab"] {
#     font-family: 'IBM Plex Mono', monospace !important; font-size: 0.72rem !important;
#     letter-spacing: 0.1em !important; text-transform: uppercase !important;
#     color: #4A6070 !important; padding: 0.6rem 1.2rem !important;
#     background: transparent !important; border: none !important;
#     border-bottom: 2px solid transparent !important;
#   }
#   [data-testid="stTabs"] [aria-selected="true"] {
#     color: #3B9EFF !important; border-bottom: 2px solid #3B9EFF !important;
#     background: transparent !important;
#   }

#   .result-card {
#     background: #0E1620; border: 1px solid #1C2A38;
#     border-radius: 6px; padding: 1.4rem; margin-bottom: 1rem;
#   }
#   .result-card.recommended { border-color: #3B9EFF55; box-shadow: 0 0 20px #3B9EFF11; }

#   .step-row {
#     display: grid; grid-template-columns: 36px 140px 110px 1fr;
#     gap: 0.8rem; align-items: start;
#     padding: 0.55rem 0; border-bottom: 1px solid #111D2A; font-size: 0.82rem;
#   }
#   .step-row:last-child { border-bottom: none; }
#   .step-num   { font-family: 'IBM Plex Mono', monospace; color: #3B9EFF; font-size: 0.72rem; padding-top: 1px; }
#   .step-tool  { font-weight: 500; color: #EEF2F7; }
#   .step-speed { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #4A8070; padding-top: 1px; }
#   .step-desc  { color: #8AA0B0; line-height: 1.5; }

#   .reasoning-block {
#     background: #080C10; border: 1px solid #1C2A38; border-radius: 4px;
#     padding: 1rem; font-size: 0.8rem; color: #6A8090; line-height: 1.7;
#     font-family: 'IBM Plex Mono', monospace; white-space: pre-wrap;
#     max-height: 260px; overflow-y: auto; margin-top: 0.8rem;
#   }

#   .status-row {
#     display: flex; align-items: center; gap: 10px;
#     padding: 0.5rem 0; font-size: 0.8rem; font-family: 'IBM Plex Mono', monospace;
#   }
#   .dot-pending { color: #2A3A4A; }
#   .dot-running { color: #E0A030; }
#   .dot-done    { color: #3DBC78; }
#   .dot-error   { color: #E05050; }

#   .err-box {
#     background: #1E0B0B; border: 1px solid #5A1515; border-radius: 4px;
#     padding: 0.8rem 1rem; font-size: 0.78rem; color: #C06060;
#     font-family: 'IBM Plex Mono', monospace;
#   }

#   hr { border-color: #1C2A38; margin: 1.5rem 0; }
#   [data-testid="stImage"] img { border-radius: 4px; border: 1px solid #1C2A38; }
#   [data-testid="stExpander"] { border: 1px solid #1C2A38 !important; background: #0E1620 !important; border-radius: 5px !important; }
#   [data-testid="stExpander"] summary { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.1em; text-transform: uppercase; color: #4A6070 !important; }
# </style>
# """, unsafe_allow_html=True)


# # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# # ✏️  CHANGE RECOMMENDED TECHNIQUES HERE
# #
# #   Once you finish evaluation and find a clear winner per complexity level,
# #   just swap the value on the right. Nothing else in the app needs to change.
# #
# #   Available keys:
# #     "zero_shot"   → Zero-Shot with Context
# #     "cot"         → Chain of Thought
# #     "guided_cot"  → Guided Chain of Thought
# #     "tot"         → Tree of Thought
# #     "got"         → Graph of Thought
# # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# RECOMMENDED = {
#     "Simple":  "zero_shot",    # ← swap after evaluation
#     "Medium":  "guided_cot",   # ← swap after evaluation
#     "Complex": "got",          # ← swap after evaluation
# }

# # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# # ✏️  CARD DISPLAY INFO (label shown on each complexity card)
# #     Keep "label" in sync with whatever key you set in RECOMMENDED above.
# # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMPLEXITY_INFO = {
#     "Simple": {
#         "badge_class": "badge-simple",
#         "label": "Zero-Shot",          # ← update to match RECOMMENDED["Simple"]
#         "desc":  "Direct features, minimal operations",
#     },
#     "Medium": {
#         "badge_class": "badge-medium",
#         "label": "Guided CoT",         # ← update to match RECOMMENDED["Medium"]
#         "desc":  "Multi-diameter steps, standard sequences",
#     },
#     "Complex": {
#         "badge_class": "badge-complex",
#         "label": "Graph of Thought",   # ← update to match RECOMMENDED["Complex"]
#         "desc":  "Tapers, grooving, dependency graphs",
#     },
# }

# # ✏️  DEFAULT CONTEXT sent silently to every technique (no input box in UI)
# DEFAULT_CONTEXT = "Analyze for Step Turning, Tapering, Grooving and other features."

# # ── Technique registry (display order) ───────────────────────────────────────
# TECHNIQUES = [
#     ("zero_shot",  "Zero-Shot"),
#     ("cot",        "Chain of Thought"),
#     ("guided_cot", "Guided CoT"),
#     ("tot",        "Tree of Thought"),
#     ("got",        "Graph of Thought"),
# ]

# # ── Session state init ────────────────────────────────────────────────────────
# if "complexity" not in st.session_state:
#     st.session_state.complexity = None
# if "results" not in st.session_state:
#     st.session_state.results = {}
# if "generated" not in st.session_state:
#     st.session_state.generated = False

# # ── Header ────────────────────────────────────────────────────────────────────
# st.markdown("""
# <div class="top-bar">
#   <span class="top-bar-icon">⚙</span>
#   <span class="top-bar-title">CNC · AI &nbsp;Workflow Generator</span>
#   <span class="top-bar-sub">BTech Final Year Project — Mechanical Engineering</span>
# </div>
# """, unsafe_allow_html=True)

# # ── Layout ────────────────────────────────────────────────────────────────────
# col_left, col_right = st.columns([1.1, 0.9], gap="large")

# with col_left:

#     # ── 01: Complexity ────────────────────────────────────────────────────────
#     st.markdown('<div class="section-label">01 — Part Complexity</div>', unsafe_allow_html=True)

#     c1, c2, c3 = st.columns(3)
#     for col, level in zip([c1, c2, c3], ["Simple", "Medium", "Complex"]):
#         info = COMPLEXITY_INFO[level]
#         with col:
#             active_class = "active" if st.session_state.complexity == level else ""
#             st.markdown(f"""
#             <div class="complexity-card {active_class}">
#               <div><span class="card-badge {info['badge_class']}">{level}</span></div>
#               <div class="card-name">{level}</div>
#               <div class="card-method">→ {info['label']}</div>
#               <div class="card-desc">{info['desc']}</div>
#             </div>
#             """, unsafe_allow_html=True)
#             if st.button(level, key=f"btn_{level}", use_container_width=True):
#                 st.session_state.complexity = level
#                 st.session_state.generated  = False
#                 st.session_state.results    = {}
#                 st.rerun()

#     if st.session_state.complexity:
#         level     = st.session_state.complexity
#         rec_label = COMPLEXITY_INFO[level]["label"]
#         st.markdown(f"""
#         <div class="rec-banner" style="margin-top:1rem;">
#           <span>✦</span>
#           <span class="rec-label">Recommended</span>
#           <span class="rec-value">{rec_label}</span>
#           <span style="color:#4A6070;font-size:0.75rem;margin-left:auto;">
#             All 5 techniques will run — this one is highlighted
#           </span>
#         </div>
#         """, unsafe_allow_html=True)

#     # ── 02: Upload ────────────────────────────────────────────────────────────
#     st.markdown('<div class="section-label">02 — Engineering Drawing</div>', unsafe_allow_html=True)
#     uploaded_file = st.file_uploader(
#         "Upload drawing",
#         type=["png", "jpg", "jpeg"],
#         label_visibility="collapsed",
#     )

#     # ── 03: Generate ──────────────────────────────────────────────────────────
#     st.markdown('<div class="section-label">03 — Generate</div>', unsafe_allow_html=True)
#     can_generate = uploaded_file is not None and st.session_state.complexity is not None
#     generate_btn = st.button("⚙  Generate All Workflows", disabled=not can_generate)

# with col_right:
#     st.markdown('<div class="section-label">Drawing Preview</div>', unsafe_allow_html=True)
#     if uploaded_file:
#         st.image(uploaded_file, use_container_width=True)
#     else:
#         st.markdown("""
#         <div style="border:1px dashed #1C2A38;border-radius:6px;height:320px;
#                     display:flex;align-items:center;justify-content:center;
#                     color:#2A3A4A;font-family:'IBM Plex Mono',monospace;font-size:0.75rem;
#                     letter-spacing:0.1em;text-transform:uppercase;">
#           No drawing uploaded
#         </div>
#         """, unsafe_allow_html=True)

# # ── Helpers ───────────────────────────────────────────────────────────────────

# def render_result_card(container, key, label, data, is_rec, complexity):
#     """Render a single technique result into a streamlit container."""
#     with container:
#         st.markdown(f"""
#         <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.8rem;margin-top:1.6rem;">
#           <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
#             letter-spacing:0.14em;text-transform:uppercase;color:{'#3B9EFF' if is_rec else '#4A6070'};">
#             {'★ ' if is_rec else ''}{ label }
#           </span>
#           {'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;background:#0D2040;color:#3B9EFF;border:1px solid #3B9EFF44;padding:2px 8px;border-radius:3px;">Recommended</span>' if is_rec else ''}
#         </div>
#         """, unsafe_allow_html=True)

#         if "error" in data:
#             st.markdown(f'<div class="err-box">{data["error"]}</div>', unsafe_allow_html=True)
#             return

#         steps = data.get("steps", [])
#         if steps:
#             step_html = "".join(f"""
#               <div class="step-row">
#                 <span class="step-num">#{s.get('step_number','?')}</span>
#                 <span class="step-tool">{s.get('tool_name','—')}</span>
#                 <span class="step-speed">{s.get('tool_speed','—')}</span>
#                 <span class="step-desc">{s.get('description','—')}</span>
#               </div>""" for s in steps)
#             st.markdown(
#                 f'<div class="result-card {"recommended" if is_rec else ""}">{step_html}</div>',
#                 unsafe_allow_html=True,
#             )

#         plan = data.get("step_by_step_plan", "")
#         if plan:
#             with st.expander("Step-by-Step Labour Plan"):
#                 st.markdown(
#                     f"<div style='font-size:0.82rem;line-height:1.8;color:#8AA0B0;'>{plan}</div>",
#                     unsafe_allow_html=True,
#                 )

#         reasoning = data.get("reasoning") or data.get("all_reasoning_process", "")
#         if reasoning:
#             with st.expander("Model Reasoning"):
#                 st.markdown(f'<div class="reasoning-block">{reasoning}</div>', unsafe_allow_html=True)

#         st.download_button(
#             label="↓  Export JSON",
#             data=json.dumps(data, indent=4),
#             file_name=f"{key}_workflow.json",
#             mime="application/json",
#             key=f"dl_live_{key}",
#         )


# # ── Generation logic ──────────────────────────────────────────────────────────
# if generate_btn and can_generate:
#     st.session_state.generated = False
#     st.session_state.results   = {}

#     suffix = Path(uploaded_file.name).suffix
#     tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
#     tmp.write(uploaded_file.getvalue())
#     tmp.close()
#     image_path = tmp.name

#     st.markdown("---")
#     st.markdown('<div class="section-label">Generating Workflows</div>', unsafe_allow_html=True)

#     total        = len(TECHNIQUES)
#     progress_bar = st.progress(0, text="")
#     verb_slot    = st.empty()          # verbose one-liner below bar
#     status_slots = {k: st.empty() for k, _ in TECHNIQUES}

#     # Pre-allocate result card containers so they appear in order
#     result_containers = {k: st.container() for k, _ in TECHNIQUES}

#     recommended_key = RECOMMENDED.get(st.session_state.complexity or "", "")

#     def render_status(key, label, state, err=None):
#         icons = {"pending": "○", "running": "◎", "done": "●", "error": "✕"}
#         cls   = {"pending": "dot-pending", "running": "dot-running",
#                  "done": "dot-done", "error": "dot-error"}
#         msg   = f" — {err}" if err else ""
#         status_slots[key].markdown(
#             f'<div class="status-row"><span class="{cls[state]}">{icons[state]}</span>'
#             f'<span>{label}{msg}</span></div>',
#             unsafe_allow_html=True,
#         )

#     def set_verb(msg):
#         verb_slot.markdown(
#             f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;'
#             f'color:#4A6070;padding:0.2rem 0 0.6rem 0;">{msg}</div>',
#             unsafe_allow_html=True,
#         )

#     for key, label in TECHNIQUES:
#         render_status(key, label, "pending")

#     # Import runners
#     runners = {}
#     try:
#         from zero_shot_with_context import run_zero_shot_workflow_with_context
#         runners["zero_shot"] = lambda ip, ctx: run_zero_shot_workflow_with_context(ip, ctx)
#     except Exception:
#         runners["zero_shot"] = None
#     try:
#         from chain_of_thought import run_cot_workflow_with_context
#         runners["cot"] = lambda ip, ctx: run_cot_workflow_with_context(ip, ctx)
#     except Exception:
#         runners["cot"] = None
#     try:
#         from guided_cot import run_guided_cot
#         runners["guided_cot"] = lambda ip, ctx: run_guided_cot(ip, ctx)
#     except Exception:
#         runners["guided_cot"] = None
#     try:
#         from tree_of_thought import run_tot
#         runners["tot"] = lambda ip, ctx: run_tot(ip, ctx)
#     except Exception:
#         runners["tot"] = None
#     try:
#         from graph_of_thought import run_got
#         runners["got"] = lambda ip, ctx: run_got(ip, ctx)
#     except Exception:
#         runners["got"] = None

#     # Run each technique, update progress live
#     for i, (key, label) in enumerate(TECHNIQUES):
#         render_status(key, label, "running")
#         set_verb(f"[{i+1}/{total}]  Sending {label} prompt to model...")
#         progress_bar.progress((i) / total, text=f"{label} — waiting for model response...")

#         runner = runners.get(key)
#         if runner is None:
#             err_msg = (
#                 f"Could not import '{key}'. Make sure app.py is in the same directory as your "
#                 "workflow .py files and all dependencies are installed (langchain, pydantic, "
#                 "google-generativeai). Also confirm src/utils.py is accessible."
#             )
#             render_status(key, label, "error", "module not found")
#             set_verb(f"[{i+1}/{total}]  ✕ {label} — import failed")
#             st.session_state.results[key] = {"error": err_msg}
#             render_result_card(result_containers[key], key, label,
#                                {"error": err_msg}, key == recommended_key,
#                                st.session_state.complexity)
#             progress_bar.progress((i + 1) / total, text="")
#             continue

#         try:
#             set_verb(f"[{i+1}/{total}]  {label} — model is generating workflow...")
#             result = runner(image_path, DEFAULT_CONTEXT)
#             data   = result.model_dump()
#             st.session_state.results[key] = data
#             n_steps = len(data.get("steps", []))
#             render_status(key, label, "done")
#             set_verb(f"[{i+1}/{total}]  ✓ {label} — {n_steps} steps generated")
#             render_result_card(result_containers[key], key, label,
#                                data, key == recommended_key,
#                                st.session_state.complexity)
#         except Exception as e:
#             err_str = str(e)
#             render_status(key, label, "error", err_str[:80])
#             set_verb(f"[{i+1}/{total}]  ✕ {label} — error")
#             st.session_state.results[key] = {"error": err_str}
#             render_result_card(result_containers[key], key, label,
#                                {"error": err_str}, key == recommended_key,
#                                st.session_state.complexity)

#         progress_bar.progress((i + 1) / total, text="")

#     os.unlink(image_path)
#     progress_bar.progress(1.0, text="All workflows generated ✓")
#     set_verb("")
#     st.session_state.generated = True

# # ── Tabbed summary (shown after full run, clean presentation view) ─────────────
# if st.session_state.generated and st.session_state.results:

#     st.markdown("---")
#     st.markdown('<div class="section-label">Summary — All Techniques</div>', unsafe_allow_html=True)

#     recommended_key = RECOMMENDED.get(st.session_state.complexity or "", "")
#     ordered    = sorted(TECHNIQUES, key=lambda x: (0 if x[0] == recommended_key else 1, x[0]))
#     tab_labels = [f"{label} ★" if key == recommended_key else label for key, label in ordered]
#     tabs       = st.tabs(tab_labels)

#     for tab, (key, label) in zip(tabs, ordered):
#         with tab:
#             data   = st.session_state.results.get(key, {})
#             is_rec = key == recommended_key

#             if "error" in data:
#                 st.markdown(f'<div class="err-box">{data["error"]}</div>', unsafe_allow_html=True)
#                 continue

#             if is_rec:
#                 st.markdown(f"""
#                 <div style="margin-bottom:1rem;">
#                   <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
#                     letter-spacing:0.12em;text-transform:uppercase;
#                     background:#0D2040;color:#3B9EFF;border:1px solid #3B9EFF44;
#                     padding:2px 8px;border-radius:3px;">
#                     ★ Recommended for {st.session_state.complexity} complexity
#                   </span>
#                 </div>
#                 """, unsafe_allow_html=True)

#             steps = data.get("steps", [])
#             if steps:
#                 step_html = "".join(f"""
#                   <div class="step-row">
#                     <span class="step-num">#{s.get('step_number','?')}</span>
#                     <span class="step-tool">{s.get('tool_name','—')}</span>
#                     <span class="step-speed">{s.get('tool_speed','—')}</span>
#                     <span class="step-desc">{s.get('description','—')}</span>
#                   </div>""" for s in steps)
#                 st.markdown(
#                     f'<div class="result-card {"recommended" if is_rec else ""}">{step_html}</div>',
#                     unsafe_allow_html=True,
#                 )

#             plan = data.get("step_by_step_plan", "")
#             if plan:
#                 with st.expander("Step-by-Step Labour Plan"):
#                     st.markdown(
#                         f"<div style='font-size:0.82rem;line-height:1.8;color:#8AA0B0;'>{plan}</div>",
#                         unsafe_allow_html=True,
#                     )

#             reasoning = data.get("reasoning") or data.get("all_reasoning_process", "")
#             if reasoning:
#                 with st.expander("Model Reasoning"):
#                     st.markdown(f'<div class="reasoning-block">{reasoning}</div>', unsafe_allow_html=True)

#             st.download_button(
#                 label="↓  Export JSON",
#                 data=json.dumps(data, indent=4),
#                 file_name=f"{key}_workflow.json",
#                 mime="application/json",
#                 key=f"dl_tab_{key}",
#             )


import streamlit as st
import json
import sys
import tempfile
import os
from pathlib import Path

# ── Path fix: ensures Python can find your workflow modules ───────────────────
# app.py must sit in the same folder as your .py workflow files.
# If you move app.py elsewhere, update this path to point at your project root.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.dirname(PROJECT_ROOT)  # one level up — contains src/
for p in [PROJECT_ROOT, REPO_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CNC·AI — Workflow Generator",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #080C10;
    color: #C8D4E0;
  }
  .stApp { background-color: #080C10; }
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 2.5rem 3rem 4rem 3rem; max-width: 1280px; }

  .top-bar {
    display: flex; align-items: center; gap: 14px;
    border-bottom: 1px solid #1C2A38;
    padding-bottom: 1.4rem; margin-bottom: 2.5rem;
  }
  .top-bar-icon { font-size: 1.6rem; color: #3B9EFF; }
  .top-bar-title {
    font-family: 'IBM Plex Mono', monospace; font-size: 1.15rem;
    font-weight: 600; letter-spacing: 0.12em; color: #EEF2F7; text-transform: uppercase;
  }
  .top-bar-sub {
    font-size: 0.78rem; color: #4A6070; letter-spacing: 0.06em;
    margin-left: auto; font-family: 'IBM Plex Mono', monospace;
  }

  .section-label {
    font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem;
    letter-spacing: 0.18em; text-transform: uppercase;
    color: #3B9EFF; margin-bottom: 0.6rem; margin-top: 2rem;
  }

  .complexity-card {
    border: 1px solid #1C2A38; border-radius: 6px;
    padding: 1.2rem 1.4rem; background: #0E1620;
  }
  .complexity-card.active { border-color: #3B9EFF; background: #0D1E30; }
  .card-badge {
    display: inline-block; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.62rem; letter-spacing: 0.14em; padding: 2px 7px;
    border-radius: 3px; margin-bottom: 0.5rem; text-transform: uppercase;
  }
  .badge-simple  { background: #0D2B1A; color: #3DBC78; border: 1px solid #1A5035; }
  .badge-medium  { background: #2B1F0A; color: #E0A030; border: 1px solid #5A3A10; }
  .badge-complex { background: #1E0B26; color: #B06EDD; border: 1px solid #4A1E6A; }
  .card-name { font-weight: 600; font-size: 1rem; color: #EEF2F7; margin-bottom: 0.25rem; }
  .card-method { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #4A6070; }
  .card-desc { font-size: 0.78rem; color: #6A8090; margin-top: 0.4rem; line-height: 1.5; }

  .rec-banner {
    display: flex; align-items: center; gap: 10px;
    background: #0D1E30; border: 1px solid #3B9EFF44;
    border-left: 3px solid #3B9EFF; border-radius: 5px;
    padding: 0.7rem 1rem; margin-bottom: 1.8rem; font-size: 0.82rem;
  }
  .rec-label { color: #3B9EFF; font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; }
  .rec-value { color: #EEF2F7; font-weight: 600; }

  [data-testid="stFileUploader"] {
    border: 1px dashed #1C2A38 !important; border-radius: 6px !important;
    background: #0E1620 !important; padding: 0.5rem !important;
  }

  .stButton > button {
    background: #3B9EFF !important; color: #000 !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
    font-weight: 600 !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; border: none !important;
    border-radius: 4px !important; padding: 0.6rem 2rem !important; width: 100%;
  }
  .stButton > button:hover { background: #5AB0FF !important; }
  .stButton > button:disabled { background: #1C2A38 !important; color: #4A6070 !important; }

  [data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent; border-bottom: 1px solid #1C2A38; gap: 0;
  }
  [data-testid="stTabs"] [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.72rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #4A6070 !important; padding: 0.6rem 1.2rem !important;
    background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important;
  }
  [data-testid="stTabs"] [aria-selected="true"] {
    color: #3B9EFF !important; border-bottom: 2px solid #3B9EFF !important;
    background: transparent !important;
  }

  .result-card {
    background: #0E1620; border: 1px solid #1C2A38;
    border-radius: 6px; padding: 1.4rem; margin-bottom: 1rem;
  }
  .result-card.recommended { border-color: #3B9EFF55; box-shadow: 0 0 20px #3B9EFF11; }

  .step-row {
    display: grid; grid-template-columns: 36px 140px 110px 1fr;
    gap: 0.8rem; align-items: start;
    padding: 0.55rem 0; border-bottom: 1px solid #111D2A; font-size: 0.82rem;
  }
  .step-row:last-child { border-bottom: none; }
  .step-num   { font-family: 'IBM Plex Mono', monospace; color: #3B9EFF; font-size: 0.72rem; padding-top: 1px; }
  .step-tool  { font-weight: 500; color: #EEF2F7; }
  .step-speed { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #4A8070; padding-top: 1px; }
  .step-desc  { color: #8AA0B0; line-height: 1.5; }

  .reasoning-block {
    background: #080C10; border: 1px solid #1C2A38; border-radius: 4px;
    padding: 1rem; font-size: 0.8rem; color: #6A8090; line-height: 1.7;
    font-family: 'IBM Plex Mono', monospace; white-space: pre-wrap;
    max-height: 260px; overflow-y: auto; margin-top: 0.8rem;
  }

  .status-row {
    display: flex; align-items: center; gap: 10px;
    padding: 0.5rem 0; font-size: 0.8rem; font-family: 'IBM Plex Mono', monospace;
  }
  .dot-pending { color: #2A3A4A; }
  .dot-running { color: #E0A030; }
  .dot-done    { color: #3DBC78; }
  .dot-error   { color: #E05050; }

  .err-box {
    background: #1E0B0B; border: 1px solid #5A1515; border-radius: 4px;
    padding: 0.8rem 1rem; font-size: 0.78rem; color: #C06060;
    font-family: 'IBM Plex Mono', monospace;
  }

  hr { border-color: #1C2A38; margin: 1.5rem 0; }
  [data-testid="stImage"] img { border-radius: 4px; border: 1px solid #1C2A38; }
  [data-testid="stExpander"] { border: 1px solid #1C2A38 !important; background: #0E1620 !important; border-radius: 5px !important; }
  [data-testid="stExpander"] summary { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.75rem !important; letter-spacing: 0.1em; text-transform: uppercase; color: #4A6070 !important; }
</style>
""", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✏️  CHANGE RECOMMENDED TECHNIQUES HERE
#
#   Once you finish evaluation and find a clear winner per complexity level,
#   just swap the value on the right. Nothing else in the app needs to change.
#
#   Available keys:
#     "zero_shot"   → Zero-Shot with Context
#     "cot"         → Chain of Thought
#     "guided_cot"  → Guided Chain of Thought
#     "tot"         → Tree of Thought
#     "got"         → Graph of Thought
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED = {
    "Simple":  "zero_shot",    # ← swap after evaluation
    "Medium":  "guided_cot",   # ← swap after evaluation
    "Complex": "got",          # ← swap after evaluation
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✏️  CARD DISPLAY INFO (label shown on each complexity card)
#     Keep "label" in sync with whatever key you set in RECOMMENDED above.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLEXITY_INFO = {
    "Simple": {
        "badge_class": "badge-simple",
        "label": "Zero-Shot",          # ← update to match RECOMMENDED["Simple"]
        "desc":  "Direct features, minimal operations",
    },
    "Medium": {
        "badge_class": "badge-medium",
        "label": "Guided CoT",         # ← update to match RECOMMENDED["Medium"]
        "desc":  "Multi-diameter steps, standard sequences",
    },
    "Complex": {
        "badge_class": "badge-complex",
        "label": "Graph of Thought",   # ← update to match RECOMMENDED["Complex"]
        "desc":  "Tapers, grooving, dependency graphs",
    },
}

# ✏️  DEFAULT CONTEXT sent silently to every technique (no input box in UI)
DEFAULT_CONTEXT = "Analyze for Step Turning, Tapering, Grooving and other features."

# ── Technique registry (display order) ───────────────────────────────────────
TECHNIQUES = [
    ("zero_shot",  "Zero-Shot"),
    ("cot",        "Chain of Thought"),
    ("guided_cot", "Guided CoT"),
    ("tot",        "Tree of Thought"),
    ("got",        "Graph of Thought"),
]

# ── Session state init ────────────────────────────────────────────────────────
if "complexity" not in st.session_state:
    st.session_state.complexity = None
if "results" not in st.session_state:
    st.session_state.results = {}
if "generated" not in st.session_state:
    st.session_state.generated = False
if "generating" not in st.session_state:
    st.session_state.generating = False
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "tmp_path" not in st.session_state:
    st.session_state.tmp_path = ""

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <span class="top-bar-icon">⚙</span>
  <span class="top-bar-title">CNC · AI &nbsp;Workflow Generator</span>
  <span class="top-bar-sub">BTech Final Year Project — Mechanical Engineering</span>
</div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1.1, 0.9], gap="large")

with col_left:

    # ── 01: Complexity ────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">01 — Part Complexity</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    for col, level in zip([c1, c2, c3], ["Simple", "Medium", "Complex"]):
        info = COMPLEXITY_INFO[level]
        with col:
            active_class = "active" if st.session_state.complexity == level else ""
            st.markdown(f"""
            <div class="complexity-card {active_class}">
              <div><span class="card-badge {info['badge_class']}">{level}</span></div>
              <div class="card-name">{level}</div>
              <div class="card-method">→ {info['label']}</div>
              <div class="card-desc">{info['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(level, key=f"btn_{level}", use_container_width=True):
                st.session_state.complexity = level
                st.session_state.generated  = False
                st.session_state.results    = {}
                st.rerun()

    if st.session_state.complexity:
        level     = st.session_state.complexity
        rec_label = COMPLEXITY_INFO[level]["label"]
        st.markdown(f"""
        <div class="rec-banner" style="margin-top:1rem;">
          <span>✦</span>
          <span class="rec-label">Recommended</span>
          <span class="rec-value">{rec_label}</span>
          <span style="color:#4A6070;font-size:0.75rem;margin-left:auto;">
            All 5 techniques will run — this one is highlighted
          </span>
        </div>
        """, unsafe_allow_html=True)

    # ── 02: Upload ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">02 — Engineering Drawing</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload drawing",
        type=["png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )

    # ── 03: Generate ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">03 — Generate</div>', unsafe_allow_html=True)
    can_generate = uploaded_file is not None and st.session_state.complexity is not None
    generate_btn = st.button("⚙  Generate All Workflows", disabled=not can_generate)

with col_right:
    st.markdown('<div class="section-label">Drawing Preview</div>', unsafe_allow_html=True)
    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)
    else:
        st.markdown("""
        <div style="border:1px dashed #1C2A38;border-radius:6px;height:320px;
                    display:flex;align-items:center;justify-content:center;
                    color:#2A3A4A;font-family:'IBM Plex Mono',monospace;font-size:0.75rem;
                    letter-spacing:0.1em;text-transform:uppercase;">
          No drawing uploaded
        </div>
        """, unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def render_result_card(container, key, label, data, is_rec, complexity):
    """Render a single technique result into a streamlit container."""
    with container:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:0.8rem;margin-top:1.6rem;">
          <span style="font-family:'IBM Plex Mono',monospace;font-size:0.68rem;
            letter-spacing:0.14em;text-transform:uppercase;color:{'#3B9EFF' if is_rec else '#4A6070'};">
            {'★ ' if is_rec else ''}{ label }
          </span>
          {'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.58rem;letter-spacing:0.12em;text-transform:uppercase;background:#0D2040;color:#3B9EFF;border:1px solid #3B9EFF44;padding:2px 8px;border-radius:3px;">Recommended</span>' if is_rec else ''}
        </div>
        """, unsafe_allow_html=True)

        if "error" in data:
            st.markdown(f'<div class="err-box">{data["error"]}</div>', unsafe_allow_html=True)
            return

        steps = data.get("steps", [])
        if steps:
            step_html = "".join(f"""
              <div class="step-row">
                <span class="step-num">#{s.get('step_number','?')}</span>
                <span class="step-tool">{s.get('tool_name','—')}</span>
                <span class="step-speed">{s.get('tool_speed','—')}</span>
                <span class="step-desc">{s.get('description','—')}</span>
              </div>""" for s in steps)
            st.markdown(
                f'<div class="result-card {"recommended" if is_rec else ""}">{step_html}</div>',
                unsafe_allow_html=True,
            )

        plan = data.get("step_by_step_plan", "")
        if plan:
            with st.expander("Step-by-Step Labour Plan"):
                st.markdown(
                    f"<div style='font-size:0.82rem;line-height:1.8;color:#8AA0B0;'>{plan}</div>",
                    unsafe_allow_html=True,
                )

        reasoning = data.get("reasoning") or data.get("all_reasoning_process", "")
        if reasoning:
            with st.expander("Model Reasoning"):
                st.markdown(f'<div class="reasoning-block">{reasoning}</div>', unsafe_allow_html=True)

        st.download_button(
            label="↓  Export JSON",
            data=json.dumps(data, indent=4),
            file_name=f"{key}_workflow.json",
            mime="application/json",
            key=f"dl_live_{key}",
        )


# ── Import runners once (cached across reruns) ───────────────────────────────
@st.cache_resource
def load_runners():
    runners = {}
    try:
        from zero_shot_with_context import run_zero_shot_workflow_with_context
        runners["zero_shot"] = lambda ip, ctx: run_zero_shot_workflow_with_context(ip, ctx)
    except Exception:
        runners["zero_shot"] = None
    try:
        from chain_of_thought import run_cot_workflow_with_context
        runners["cot"] = lambda ip, ctx: run_cot_workflow_with_context(ip, ctx)
    except Exception:
        runners["cot"] = None
    try:
        from guided_cot import run_guided_cot
        runners["guided_cot"] = lambda ip, ctx: run_guided_cot(ip, ctx)
    except Exception:
        runners["guided_cot"] = None
    try:
        from tree_of_thought import run_tot
        runners["tot"] = lambda ip, ctx: run_tot(ip, ctx)
    except Exception:
        runners["tot"] = None
    try:
        from graph_of_thought import run_got
        runners["got"] = lambda ip, ctx: run_got(ip, ctx)
    except Exception:
        runners["got"] = None
    return runners


# ── Kick off generation when button pressed ───────────────────────────────────
if generate_btn and can_generate:
    # Save image to a temp file that persists across reruns
    suffix = Path(uploaded_file.name).suffix
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded_file.getvalue())
    tmp.close()

    st.session_state.results     = {}
    st.session_state.current_idx = 0
    st.session_state.generating  = True
    st.session_state.tmp_path    = tmp.name
    st.rerun()


# ── Progress bar + status (shown while generating) ────────────────────────────
total = len(TECHNIQUES)

if st.session_state.generating or st.session_state.generated:
    st.markdown("---")

    done_count = len(st.session_state.results)
    pct        = done_count / total

    if st.session_state.generating:
        idx          = st.session_state.get("current_idx", 0)
        _, cur_label = TECHNIQUES[min(idx, total - 1)]
        bar_text     = f"Running {cur_label}...  ({done_count}/{total} complete)"
    else:
        bar_text = f"All {total} workflows generated ✓"

    st.progress(pct, text=bar_text)

    # Status dots row
    dot_html = ""
    for i, (key, label) in enumerate(TECHNIQUES):
        if key in st.session_state.results:
            data = st.session_state.results[key]
            if "error" in data:
                icon, cls = "✕", "dot-error"
            else:
                n = len(data.get("steps", []))
                icon, cls = f"● {n} steps", "dot-done"
        elif st.session_state.generating and i == st.session_state.get("current_idx", 0):
            icon, cls = "◎ running", "dot-running"
        else:
            icon, cls = "○", "dot-pending"
        dot_html += (
            f'<span class="{cls}" style="font-family:''IBM Plex Mono'',monospace;'
            f'font-size:0.72rem;margin-right:1.6rem;">{icon}&nbsp;{label}</span>'
        )
    st.markdown(f'<div style="padding:0.4rem 0 1.2rem 0;">{dot_html}</div>',
                unsafe_allow_html=True)


# ── Run ONE technique per rerun, then rerun again ─────────────────────────────
if st.session_state.generating:
    idx = st.session_state.get("current_idx", 0)

    if idx < total:
        key, label = TECHNIQUES[idx]
        runners    = load_runners()
        runner     = runners.get(key)
        image_path = st.session_state.get("tmp_path", "")

        if runner is None:
            st.session_state.results[key] = {
                "error": (
                    f"Could not import '{key}'. Make sure app.py is in the same folder as your "
                    "workflow .py files, all dependencies are installed, and src/utils.py is accessible."
                )
            }
        else:
            try:
                result = runner(image_path, DEFAULT_CONTEXT)
                st.session_state.results[key] = result.model_dump()
            except Exception as e:
                st.session_state.results[key] = {"error": str(e)}

        st.session_state.current_idx = idx + 1
        st.rerun()

    else:
        # All done
        if os.path.exists(st.session_state.get("tmp_path", "")):
            os.unlink(st.session_state.tmp_path)
        st.session_state.generating = False
        st.session_state.generated  = True
        st.rerun()


# ── Tabs (render whenever generating OR generated) ────────────────────────────
if st.session_state.generating or st.session_state.generated:

    recommended_key = RECOMMENDED.get(st.session_state.complexity or "", "")
    ordered         = sorted(TECHNIQUES, key=lambda x: (0 if x[0] == recommended_key else 1, x[0]))
    tab_labels      = [f"{label} ★" if key == recommended_key else label for key, label in ordered]
    tabs            = st.tabs(tab_labels)

    current_idx = st.session_state.get("current_idx", 0)

    for tab, (key, label) in zip(tabs, ordered):
        with tab:
            technique_idx = next(i for i, (k, _) in enumerate(TECHNIQUES) if k == key)

            # ── Not started yet ───────────────────────────────────────────────
            if key not in st.session_state.results and technique_idx > current_idx - 1:
                st.markdown(
                    '<div style="color:#2A3A4A;font-family:''IBM Plex Mono'',monospace;'
                    'font-size:0.78rem;padding:2rem 0;">○ &nbsp;Waiting to start...</div>',
                    unsafe_allow_html=True,
                )
                continue

            # ── Currently running ─────────────────────────────────────────────
            if key not in st.session_state.results and technique_idx == current_idx - 1:
                with st.spinner(f"Running {label}..."):
                    st.markdown(
                        '<div style="color:#E0A030;font-family:''IBM Plex Mono'',monospace;'
                        'font-size:0.78rem;padding:1rem 0;">◎ &nbsp;Model is generating workflow...</div>',
                        unsafe_allow_html=True,
                    )
                continue

            data   = st.session_state.results.get(key, {})
            is_rec = key == recommended_key

            # ── Error ─────────────────────────────────────────────────────────
            if "error" in data:
                st.markdown(f'<div class="err-box">{data["error"]}</div>',
                            unsafe_allow_html=True)
                continue

            # ── Recommended badge ─────────────────────────────────────────────
            if is_rec:
                st.markdown(f"""
                <div style="margin-bottom:1rem;">
                  <span style="font-family:'IBM Plex Mono',monospace;font-size:0.6rem;
                    letter-spacing:0.12em;text-transform:uppercase;
                    background:#0D2040;color:#3B9EFF;border:1px solid #3B9EFF44;
                    padding:2px 8px;border-radius:3px;">
                    ★ Recommended for {st.session_state.complexity} complexity
                  </span>
                </div>
                """, unsafe_allow_html=True)

            # ── Steps table ───────────────────────────────────────────────────
            steps = data.get("steps", [])
            if steps:
                step_html = "".join(f"""
                  <div class="step-row">
                    <span class="step-num">#{s.get('step_number','?')}</span>
                    <span class="step-tool">{s.get('tool_name','—')}</span>
                    <span class="step-speed">{s.get('tool_speed','—')}</span>
                    <span class="step-desc">{s.get('description','—')}</span>
                  </div>""" for s in steps)
                st.markdown(
                    f'<div class="result-card {"recommended" if is_rec else ""}">{step_html}</div>',
                    unsafe_allow_html=True,
                )

            # ── Expanders ─────────────────────────────────────────────────────
            plan = data.get("step_by_step_plan", "")
            if plan:
                with st.expander("Step-by-Step Labour Plan"):
                    st.markdown(
                        f"<div style='font-size:0.82rem;line-height:1.8;color:#8AA0B0;'>{plan}</div>",
                        unsafe_allow_html=True,
                    )

            reasoning = data.get("reasoning") or data.get("all_reasoning_process", "")
            if reasoning:
                with st.expander("Model Reasoning"):
                    st.markdown(f'<div class="reasoning-block">{reasoning}</div>',
                                unsafe_allow_html=True)

            # ── Export ────────────────────────────────────────────────────────
            st.download_button(
                label="↓  Export JSON",
                data=json.dumps(data, indent=4),
                file_name=f"{key}_workflow.json",
                mime="application/json",
                key=f"dl_{key}",
            )