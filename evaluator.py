# """
# CNC Workflow Evaluator — Terminal Tool
# Run: python evaluator.py

# Metrics:
#   M1 — FCR  : Feature Capture Rate        (Gate — if < 1.0, WQS = 0)
#   M2 — SCS  : Sequence Correctness Score  (0–1, expert holistic)
#   M3 — WR   : Workflow Rating             (0–1, expert holistic)
#   M4 — ROA  : Reasoning–Output Alignment  (0–1, CoT/GoT/ToT only)
#   M5 — ORR  : Operational Redundancy Rate (penalty, folded into WQS)

# Final Score:
#   WQS = FCR × (1 - ORR) × (w1·SCS + w2·WR + w3·ROA)

#   Zero-Shot : w1=0.50, w2=0.50, w3=N/A
#   Others    : w1=0.35, w2=0.30, w3=0.35
# """

# import json
# import os
# import sys
# import glob
# from datetime import datetime

# PROGRESS_FILE = "output/1_evaluation/evaluation_progress.json"
# RESULTS_FILE  = "output/1_evaluation/evaluation_results.json"

# TECHNIQUES    = ["zero_shot", "cot", "guided_cot", "tot", "got"]
# CATEGORIES    = ["simple", "medium", "hard"]
# HAS_REASONING = {"cot", "guided_cot", "tot", "got"}

# RUBRIC = """
#   SCORING RUBRIC (use for SCS, TPA, ROA):
#   ┌───────┬─────────────────────────────────────────────────┐
#   │ Score │ Meaning                                         │
#   ├───────┼─────────────────────────────────────────────────┤
#   │  1.0  │ Perfect / fully correct                         │
#   │  0.75 │ Minor issues, mostly correct                    │
#   │  0.5  │ Partial — some correct, some wrong              │
#   │  0.25 │ Mostly wrong, barely usable                     │
#   │  0.0  │ Completely wrong / unusable                     │
#   └───────┴─────────────────────────────────────────────────┘
#   Valid inputs: 0.0 / 0.25 / 0.5 / 0.75 / 1.0
# """

# # ── Helpers ───────────────────────────────────────────────────────────────────

# def load_json(path):
#     with open(path, "r") as f:
#         return json.load(f)

# def save_json(path, data):
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "w") as f:
#         json.dump(data, f, indent=4)

# def load_progress():
#     if os.path.exists(PROGRESS_FILE):
#         return load_json(PROGRESS_FILE)
#     return {"completed": [], "evaluator_name": None}

# def load_results():
#     if os.path.exists(RESULTS_FILE):
#         return load_json(RESULTS_FILE)
#     return []

# def save_progress(progress):
#     save_json(PROGRESS_FILE, progress)

# def save_result(result):
#     results = load_results()
#     for i, r in enumerate(results):
#         if r["image_id"] == result["image_id"] and r["technique"] == result["technique"]:
#             results[i] = result
#             save_json(RESULTS_FILE, results)
#             return
#     results.append(result)
#     save_json(RESULTS_FILE, results)

# def get_result_files(technique, category):
#     folder  = f"output/{technique}_results"
#     pattern = os.path.join(folder, f"result_{category}_*.json")
#     return sorted(glob.glob(pattern))

# def ask(prompt, valid=None, allow_quit=True):
#     while True:
#         val = input(prompt).strip()
#         if allow_quit and val.lower() == "q":
#             print("\n[*] Progress saved. Exiting.")
#             sys.exit(0)
#         if valid is None:
#             return val
#         if val in valid:
#             return val
#         print(f"    Invalid input. Choose from {valid} or 'q' to quit.")

# def ask_rubric_score(prompt):
#     """Ask for a rubric score: 0.0, 0.25, 0.5, 0.75, or 1.0"""
#     valid = ["0", "0.0", "0.25", "0.5", "0.75", "1", "1.0"]
#     mapping = {"0": 0.0, "0.0": 0.0, "0.25": 0.25, "0.5": 0.5,
#                "0.75": 0.75, "1": 1.0, "1.0": 1.0}
#     while True:
#         val = input(prompt).strip()
#         if val.lower() == "q":
#             print("\n[*] Progress saved. Exiting.")
#             sys.exit(0)
#         if val in mapping:
#             return mapping[val]
#         print(f"    Invalid. Enter one of: 0.0 / 0.25 / 0.5 / 0.75 / 1.0")

# def ask_int(prompt, min_val=0):
#     while True:
#         val = input(prompt).strip()
#         if val.lower() == "q":
#             print("\n[*] Progress saved. Exiting.")
#             sys.exit(0)
#         try:
#             i = int(val)
#             if i >= min_val:
#                 return i
#             print(f"    Enter a value >= {min_val}")
#         except ValueError:
#             print("    Invalid number. Try again.")

# def print_divider(char="─", width=60):
#     print(f"  {char * width}")

# def wrap_print(text, indent="  ", width=72):
#     words = text.split()
#     line  = indent
#     for word in words:
#         if len(line) + len(word) + 1 > width:
#             print(line)
#             line = indent + word + " "
#         else:
#             line += word + " "
#     if line.strip():
#         print(line)


# # ── Compute WQS ───────────────────────────────────────────────────────────────

# def compute_wqs(fcr, scs, wr, roa, orr, has_reasoning):
#     """
#     WQS = FCR × (1 - ORR) × (w1·SCS + w2·WR + w3·ROA)

#     Zero-Shot : w1=0.50, w2=0.50  (no ROA)
#     Others    : w1=0.35, w2=0.30, w3=0.35
#     """
#     if fcr < 1.0:
#         return 0.0

#     if has_reasoning and roa is not None:
#         weighted = 0.35 * scs + 0.30 * wr + 0.35 * roa
#     else:
#         weighted = 0.50 * scs + 0.50 * wr

#     return round(fcr * (1 - orr) * weighted, 4)


# # ── Display workflow ───────────────────────────────────────────────────────────

# def display_workflow(data, technique):
#     steps       = data.get("steps", [])
#     reasoning   = data.get("reasoning", None) or data.get("all_reasoning_process", None)
#     plan        = data.get("step_by_step_plan", None)
#     total_steps = len(steps)

#     print_divider("─")
#     print(f"  STEPS ({total_steps} total):")
#     print_divider("─")
#     for s in steps:
#         print(f"\n  Step {s['step_number']}: {s['tool_name']} @ {s.get('tool_speed', 'N/A')}")
#         print(f"  → {s['description']}")

#     if reasoning and technique in HAS_REASONING:
#         print(f"\n")
#         print_divider("─")
#         print("  REASONING:")
#         print_divider("─")
#         wrap_print(reasoning)

#     if plan and technique in HAS_REASONING:
#         print(f"\n")
#         print_divider("─")
#         print("  STEP-BY-STEP PLAN:")
#         print_divider("─")
#         for line in plan.split("\n"):
#             print(f"  {line.strip()}")

#     return total_steps


# # ── Evaluate one workflow ──────────────────────────────────────────────────────

# def evaluate_workflow(image_id, technique, filepath, evaluator_name):
#     print(f"\n{'=' * 62}")
#     print(f"  Image     : {image_id}")
#     print(f"  File      : {filepath}")
#     print(f"  Technique : {technique.upper()}")
#     print(f"{'=' * 62}")

#     try:
#         data        = load_json(filepath)
#         total_steps = display_workflow(data, technique)
#     except Exception as e:
#         print(f"  [ERROR] Could not load file: {e}")
#         return None

#     print(f"\n")
#     print(RUBRIC)
#     print_divider("─")
#     print("  Type 'q' at any prompt to save progress and quit.\n")

#     # ── M1: FCR ───────────────────────────────────────────────────────────────
#     print("  [M1] FEATURE CAPTURE RATE (FCR) — Gate Metric")
#     print("  List all geometric features in the drawing (chamfers, tapers, steps).")
#     print("  Then count how many are addressed in the steps above.\n")
#     total_features = ask_int("  Total features in drawing : ", min_val=1)
#     addressed      = ask_int("  Features addressed        : ", min_val=0)
#     addressed      = min(addressed, total_features)
#     fcr            = round(addressed / total_features, 4)
#     print(f"  → FCR = {addressed}/{total_features} = {fcr}")

#     if fcr < 1.0:
#         missed = total_features - addressed
#         print(f"\n  ✗ FCR < 1.0 — {missed} feature(s) missed.")
#         print(f"  → WQS = 0.0  (workflow is incomplete, evaluation stops here)")
#         print_divider("─")

#         result = {
#             "image_id"       : image_id,
#             "technique"      : technique,
#             "evaluator"      : evaluator_name,
#             "file"           : filepath,
#             "timestamp"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "total_steps"    : total_steps,
#             "total_features" : total_features,
#             "addressed"      : addressed,
#             "fcr"            : fcr,
#             "scs"            : None,
#             "tpa"            : None,
#             "roa"            : None,
#             "orr"            : None,
#             "wqs"            : 0.0,
#             "notes"          : input("\n  Observations (Enter to skip): ").strip()
#         }
#         save_result(result)
#         print(f"\n  [*] Saved to {RESULTS_FILE}")
#         return result

#     print(f"  ✓ All features captured. Proceeding.\n")

#     # ── M2: SCS ───────────────────────────────────────────────────────────────
#     print("  [M2] SEQUENCE CORRECTNESS SCORE (SCS)")
#     print("  Is the operation order correct?")
#     print("  (roughing → finishing, larger dia → smaller, facing → turning etc.)")
#     scs = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
#     print(f"  → SCS = {scs}\n")

#     # ── M3: WR ────────────────────────────────────────────────────────────────
#     print("  [M3] WORKFLOW RATING (WR)")
#     print("  As a machinist, how good is this workflow overall?")
#     print("  Consider tool selection, process correctness, and general quality.")
#     wr = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
#     print(f"  → WR = {wr}\n")

#     # ── M4: ROA ───────────────────────────────────────────────────────────────
#     roa = None
#     if technique in HAS_REASONING:
#         print("  [M4] REASONING–OUTPUT ALIGNMENT (ROA)")
#         print("  Did the reasoning actually lead to and justify the steps?")
#         print("  Read the reasoning above and judge holistically.")
#         roa = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
#         print(f"  → ROA = {roa}\n")
#     else:
#         print("  [M4] ROA — N/A (Zero-Shot has no reasoning)\n")

#     # ── M5: ORR ───────────────────────────────────────────────────────────────
#     print("  [M5] OPERATIONAL REDUNDANCY RATE (ORR)")
#     print("  How many steps are unnecessary, repeated, or would cause problems?")
#     redundant = ask_int("  Redundant steps : ", min_val=0)
#     redundant = min(redundant, total_steps)
#     orr       = round(redundant / total_steps, 4) if total_steps > 0 else 0.0
#     print(f"  → ORR = {redundant}/{total_steps} = {orr}\n")

#     # ── WQS ───────────────────────────────────────────────────────────────────
#     wqs = compute_wqs(fcr, scs, wr, roa, orr, technique in HAS_REASONING)

#     print_divider("═")
#     print(f"  WORKFLOW QUALITY SCORE (WQS) = {wqs}")
#     if technique in HAS_REASONING:
#         print(f"  Formula : FCR × (1 - ORR) × (0.35·SCS + 0.30·WR + 0.35·ROA)")
#         print(f"  Values  : {fcr} × {round(1-orr, 4)} × (0.35×{scs} + 0.30×{wr} + 0.35×{roa})")
#     else:
#         print(f"  Formula : FCR × (1 - ORR) × (0.50·SCS + 0.50·WR)")
#         print(f"  Values  : {fcr} × {round(1-orr, 4)} × (0.50×{scs} + 0.50×{wr})")
#     print_divider("═")

#     notes = input("\n  Observations (Enter to skip): ").strip()

#     result = {
#         "image_id"       : image_id,
#         "technique"      : technique,
#         "evaluator"      : evaluator_name,
#         "file"           : filepath,
#         "timestamp"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "total_steps"    : total_steps,
#         "total_features" : total_features,
#         "addressed"      : addressed,
#         "fcr"            : fcr,
#         "scs"            : scs,
#         "wr"             : wr,
#         "roa"            : roa,
#         "orr"            : orr,
#         "wqs"            : wqs,
#         "notes"          : notes
#     }

#     save_result(result)
#     print(f"\n  [*] Saved to {RESULTS_FILE}")
#     return result


# # ── Main ──────────────────────────────────────────────────────────────────────

# def main():
#     print("\n" + "=" * 62)
#     print("   CNC WORKFLOW EVALUATOR")
#     print("=" * 62)
#     print("  Type 'q' at any prompt to save progress and quit.\n")

#     progress = load_progress()

#     # Evaluator name
#     if progress["evaluator_name"]:
#         print(f"  Welcome back, {progress['evaluator_name']}!")
#         change = ask("  Continue as same evaluator? (y/n): ", valid=["y", "n"])
#         if change == "n":
#             progress["evaluator_name"] = None

#     if not progress["evaluator_name"]:
#         name = input("  Enter your name: ").strip() or "Evaluator"
#         progress["evaluator_name"] = name
#         save_progress(progress)

#     evaluator_name = progress["evaluator_name"]
#     completed      = set(progress["completed"])

#     # Build task list
#     image_map = {}
#     for technique in TECHNIQUES:
#         for category in CATEGORIES:
#             for filepath in get_result_files(technique, category):
#                 basename = os.path.basename(filepath)
#                 parts    = basename.replace("result_", "").split("_")
#                 image_id = f"{parts[0]}_{parts[1]}"
#                 if image_id not in image_map:
#                     image_map[image_id] = {}
#                 image_map[image_id][technique] = filepath

#     def image_sort_key(img_id):
#         cat   = img_id.split("_")[0]
#         num   = img_id.split("_")[1]
#         order = {"simple": 0, "medium": 1, "hard": 2}
#         return (int(num), order.get(cat, 99))

#     tasks = []
#     for image_id in sorted(image_map.keys(), key=image_sort_key):
#         for technique in TECHNIQUES:
#             filepath = image_map[image_id].get(technique)
#             if filepath:
#                 task_key = f"{image_id}__{technique}"
#                 tasks.append((task_key, image_id, technique, filepath))

#     remaining = [t for t in tasks if t[0] not in completed]
#     total     = len(tasks)
#     done      = len(completed)

#     print(f"  Progress  : {done}/{total} evaluations completed")
#     print(f"  Remaining : {len(remaining)}")

#     if not remaining:
#         print("\n  All evaluations complete!")
#         print(f"  Results saved in: {RESULTS_FILE}")
#         return

#     print("\n  Press Enter to start, or 'q' to quit.")
#     ask("  > ", valid=None, allow_quit=True)

#     for task_key, image_id, technique, filepath in remaining:
#         result = evaluate_workflow(image_id, technique, filepath, evaluator_name)

#         if result is not None:
#             completed.add(task_key)
#             progress["completed"] = list(completed)
#             save_progress(progress)

#         done = len(completed)
#         print(f"\n  Progress: {done}/{total} done")

#         if done < total:
#             cont = ask("\n  Continue to next? (y/n): ", valid=["y", "n"])
#             if cont == "n":
#                 print("\n[*] Progress saved. Resume anytime by running this script again.")
#                 sys.exit(0)

#     print("\n" + "=" * 62)
#     print(f"  ALL DONE! Results saved to: {RESULTS_FILE}")
#     print("=" * 62)


# if __name__ == "__main__":
#     main()

"""
CNC Workflow Evaluator — Terminal Tool
Run: python evaluator.py

Metrics:
  M1 — FCR  : Feature Capture Rate        (Gate — if < 1.0, WQS = 0)
  M2 — SCS  : Sequence Correctness Score  (0–1, expert holistic)
  M3 — WR   : Workflow Rating             (0–1, expert holistic)
  M4 — ROA  : Reasoning–Output Alignment  (0–1, CoT/GoT/ToT only)
  M5 — ORR  : Operational Redundancy Rate (penalty, folded into WQS)

Final Score:
  WQS = FCR × (1 - ORR) × (w1·SCS + w2·WR + w3·ROA)

  Zero-Shot : w1=0.50, w2=0.50, w3=N/A
  Others    : w1=0.35, w2=0.30, w3=0.35
"""

import json
import os
import sys
import glob
from datetime import datetime

PROGRESS_FILE = "output/1_evaluation/evaluation_progress.json"
RESULTS_FILE  = "output/1_evaluation/evaluation_results.json"

TECHNIQUES    = ["zero_shot", "cot", "guided_cot", "tot", "got"]
CATEGORIES    = ["simple", "medium", "hard"]
HAS_REASONING = {"cot", "guided_cot", "tot", "got"}

RUBRIC = """
  SCORING RUBRIC (use for SCS, TPA, ROA):
  ┌───────┬─────────────────────────────────────────────────┐
  │ Score │ Meaning                                         │
  ├───────┼─────────────────────────────────────────────────┤
  │  1.0  │ Perfect / fully correct                         │
  │  0.75 │ Minor issues, mostly correct                    │
  │  0.5  │ Partial — some correct, some wrong              │
  │  0.25 │ Mostly wrong, barely usable                     │
  │  0.0  │ Completely wrong / unusable                     │
  └───────┴─────────────────────────────────────────────────┘
  Valid inputs: 0.0 / 0.25 / 0.5 / 0.75 / 1.0
"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        return load_json(PROGRESS_FILE)
    return {"completed": [], "evaluator_name": None}

def load_results():
    if os.path.exists(RESULTS_FILE):
        return load_json(RESULTS_FILE)
    return []

def save_progress(progress):
    save_json(PROGRESS_FILE, progress)

def save_result(result):
    results = load_results()
    for i, r in enumerate(results):
        if r["image_id"] == result["image_id"] and r["technique"] == result["technique"]:
            results[i] = result
            save_json(RESULTS_FILE, results)
            return
    results.append(result)
    save_json(RESULTS_FILE, results)

def get_result_files(technique, category):
    folder  = f"output/{technique}_results"
    pattern = os.path.join(folder, f"result_{category}_*.json")
    return sorted(glob.glob(pattern))

def ask(prompt, valid=None, allow_quit=True):
    while True:
        val = input(prompt).strip()
        if allow_quit and val.lower() == "q":
            print("\n[*] Progress saved. Exiting.")
            sys.exit(0)
        if valid is None:
            return val
        if val in valid:
            return val
        print(f"    Invalid input. Choose from {valid} or 'q' to quit.")

def ask_rubric_score(prompt):
    """Ask for a rubric score: 0.0, 0.25, 0.5, 0.75, or 1.0"""
    valid = ["0", "0.0", "0.25", "0.5", "0.75", "1", "1.0"]
    mapping = {"0": 0.0, "0.0": 0.0, "0.25": 0.25, "0.5": 0.5,
               "0.75": 0.75, "1": 1.0, "1.0": 1.0}
    while True:
        val = input(prompt).strip()
        if val.lower() == "q":
            print("\n[*] Progress saved. Exiting.")
            sys.exit(0)
        if val in mapping:
            return mapping[val]
        print(f"    Invalid. Enter one of: 0.0 / 0.25 / 0.5 / 0.75 / 1.0")

def ask_int(prompt, min_val=0):
    while True:
        val = input(prompt).strip()
        if val.lower() == "q":
            print("\n[*] Progress saved. Exiting.")
            sys.exit(0)
        try:
            i = int(val)
            if i >= min_val:
                return i
            print(f"    Enter a value >= {min_val}")
        except ValueError:
            print("    Invalid number. Try again.")

def print_divider(char="─", width=60):
    print(f"  {char * width}")

def wrap_print(text, indent="  ", width=72):
    words = text.split()
    line  = indent
    for word in words:
        if len(line) + len(word) + 1 > width:
            print(line)
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        print(line)


# ── Compute WQS ───────────────────────────────────────────────────────────────

def compute_wqs(fcr, scs, wr, roa, orr, has_reasoning):
    """
    WQS = FCR × (1 - ORR) × (w1·SCS + w2·WR + w3·ROA)

    Zero-Shot : w1=0.50, w2=0.50  (no ROA)
    Others    : w1=0.35, w2=0.30, w3=0.35
    """
    if fcr < 1.0:
        return 0.0

    if has_reasoning and roa is not None:
        weighted = 0.35 * scs + 0.30 * wr + 0.35 * roa
    else:
        weighted = 0.50 * scs + 0.50 * wr

    return round(fcr * (1 - orr) * weighted, 4)


# ── Display workflow ───────────────────────────────────────────────────────────

def display_workflow(data, technique):
    steps       = data.get("steps", [])
    reasoning   = data.get("reasoning", None) or data.get("all_reasoning_process", None)
    plan        = data.get("step_by_step_plan", None)
    total_steps = len(steps)

    print_divider("─")
    print(f"  STEPS ({total_steps} total):")
    print_divider("─")
    for s in steps:
        print(f"\n  Step {s['step_number']}: {s['tool_name']} @ {s.get('tool_speed', 'N/A')}")
        print(f"  → {s['description']}")

    if reasoning and technique in HAS_REASONING:
        print(f"\n")
        print_divider("─")
        print("  REASONING:")
        print_divider("─")
        wrap_print(reasoning)

    if plan and technique in HAS_REASONING:
        print(f"\n")
        print_divider("─")
        print("  STEP-BY-STEP PLAN:")
        print_divider("─")
        for line in plan.split("\n"):
            print(f"  {line.strip()}")

    return total_steps


# ── Evaluate one workflow ──────────────────────────────────────────────────────

def evaluate_workflow(image_id, technique, filepath, evaluator_name):
    print(f"\n{'=' * 62}")
    print(f"  Image     : {image_id}")
    print(f"  File      : {filepath}")
    print(f"  Technique : {technique.upper()}")
    print(f"{'=' * 62}")

    try:
        data        = load_json(filepath)
        total_steps = display_workflow(data, technique)
    except Exception as e:
        print(f"  [ERROR] Could not load file: {e}")
        return None

    print(f"\n")
    print(RUBRIC)
    print_divider("─")
    print("  Type 'q' at any prompt to save progress and quit.\n")

    # ── M1: FCR ───────────────────────────────────────────────────────────────
    print("  [M1] FEATURE CAPTURE RATE (FCR) — Gate Metric")
    print("  List all geometric features in the drawing (chamfers, tapers, steps).")
    print("  Then count how many are addressed in the steps above.\n")
    total_features = ask_int("  Total features in drawing : ", min_val=1)
    addressed      = ask_int("  Features addressed        : ", min_val=0)
    addressed      = min(addressed, total_features)
    fcr            = round(addressed / total_features, 4)
    print(f"  → FCR = {addressed}/{total_features} = {fcr}")

    if fcr < 1.0:
        missed = total_features - addressed
        print(f"\n  ✗ FCR < 1.0 — {missed} feature(s) missed.")
        print(f"  → WQS = 0.0  (workflow is incomplete, evaluation stops here)")
        print_divider("─")

        result = {
            "image_id"       : image_id,
            "technique"      : technique,
            "evaluator"      : evaluator_name,
            "file"           : filepath,
            "timestamp"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_steps"    : total_steps,
            "total_features" : total_features,
            "addressed"      : addressed,
            "fcr"            : fcr,
            "scs"            : None,
            "wr"             : None,
            "roa"            : None,
            "orr"            : None,
            "wqs"            : 0.0,
            "notes"          : input("\n  Observations (Enter to skip): ").strip()
        }
        save_result(result)
        print(f"\n  [*] Saved to {RESULTS_FILE}")
        return result

    print(f"  ✓ All features captured. Proceeding.\n")

    # ── M2: SCS ───────────────────────────────────────────────────────────────
    print("  [M2] SEQUENCE CORRECTNESS SCORE (SCS)")
    print("  Is the operation order correct?")
    print("  (roughing → finishing, larger dia → smaller, facing → turning etc.)")
    scs = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
    print(f"  → SCS = {scs}\n")

    # ── M3: WR ────────────────────────────────────────────────────────────────
    print("  [M3] WORKFLOW RATING (WR)")
    print("  As a machinist, how good is this workflow overall?")
    print("  Consider tool selection, process correctness, and general quality.")
    wr = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
    print(f"  → WR = {wr}\n")

    # ── M4: ROA ───────────────────────────────────────────────────────────────
    roa = None
    if technique in HAS_REASONING:
        print("  [M4] REASONING–OUTPUT ALIGNMENT (ROA)")
        print("  Did the reasoning actually lead to and justify the steps?")
        print("  Read the reasoning above and judge holistically.")
        roa = ask_rubric_score("  Score (0.0 / 0.25 / 0.5 / 0.75 / 1.0): ")
        print(f"  → ROA = {roa}\n")
    else:
        print("  [M4] ROA — N/A (Zero-Shot has no reasoning)\n")

    # ── M5: ORR ───────────────────────────────────────────────────────────────
    print("  [M5] OPERATIONAL REDUNDANCY RATE (ORR)")
    print("  How many steps are unnecessary, repeated, or would cause problems?")
    redundant = ask_int("  Redundant steps : ", min_val=0)
    redundant = min(redundant, total_steps)
    orr       = round(redundant / total_steps, 4) if total_steps > 0 else 0.0
    print(f"  → ORR = {redundant}/{total_steps} = {orr}\n")

    # ── WQS ───────────────────────────────────────────────────────────────────
    wqs = compute_wqs(fcr, scs, wr, roa, orr, technique in HAS_REASONING)

    print_divider("═")
    print(f"  WORKFLOW QUALITY SCORE (WQS) = {wqs}")
    if technique in HAS_REASONING:
        print(f"  Formula : FCR × (1 - ORR) × (0.35·SCS + 0.30·WR + 0.35·ROA)")
        print(f"  Values  : {fcr} × {round(1-orr, 4)} × (0.35×{scs} + 0.30×{wr} + 0.35×{roa})")
    else:
        print(f"  Formula : FCR × (1 - ORR) × (0.50·SCS + 0.50·WR)")
        print(f"  Values  : {fcr} × {round(1-orr, 4)} × (0.50×{scs} + 0.50×{wr})")
    print_divider("═")

    notes = input("\n  Observations (Enter to skip): ").strip()

    result = {
        "image_id"       : image_id,
        "technique"      : technique,
        "evaluator"      : evaluator_name,
        "file"           : filepath,
        "timestamp"      : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_steps"    : total_steps,
        "total_features" : total_features,
        "addressed"      : addressed,
        "fcr"            : fcr,
        "scs"            : scs,
        "wr"             : wr,
        "roa"            : roa,
        "orr"            : orr,
        "wqs"            : wqs,
        "notes"          : notes
    }

    save_result(result)
    print(f"\n  [*] Saved to {RESULTS_FILE}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 62)
    print("   CNC WORKFLOW EVALUATOR")
    print("=" * 62)
    print("  Type 'q' at any prompt to save progress and quit.\n")

    progress = load_progress()

    # Evaluator name
    if progress["evaluator_name"]:
        print(f"  Welcome back, {progress['evaluator_name']}!")
        change = ask("  Continue as same evaluator? (y/n): ", valid=["y", "n"])
        if change == "n":
            progress["evaluator_name"] = None

    if not progress["evaluator_name"]:
        name = input("  Enter your name: ").strip() or "Evaluator"
        progress["evaluator_name"] = name
        save_progress(progress)

    evaluator_name = progress["evaluator_name"]
    completed      = set(progress["completed"])

    # Build task list
    image_map = {}
    for technique in TECHNIQUES:
        for category in CATEGORIES:
            for filepath in get_result_files(technique, category):
                basename = os.path.basename(filepath)
                parts    = basename.replace("result_", "").split("_")
                image_id = f"{parts[0]}_{parts[1]}"
                if image_id not in image_map:
                    image_map[image_id] = {}
                image_map[image_id][technique] = filepath

    def image_sort_key(img_id):
        cat   = img_id.split("_")[0]
        num   = img_id.split("_")[1]
        order = {"simple": 0, "medium": 1, "hard": 2}
        return (int(num), order.get(cat, 99))

    tasks = []
    for image_id in sorted(image_map.keys(), key=image_sort_key):
        for technique in TECHNIQUES:
            filepath = image_map[image_id].get(technique)
            if filepath:
                task_key = f"{image_id}__{technique}"
                tasks.append((task_key, image_id, technique, filepath))

    remaining = [t for t in tasks if t[0] not in completed]
    total     = len(tasks)
    done      = len(completed)

    print(f"  Progress  : {done}/{total} evaluations completed")
    print(f"  Remaining : {len(remaining)}")

    if not remaining:
        print("\n  All evaluations complete!")
        print(f"  Results saved in: {RESULTS_FILE}")
        return

    print("\n  Press Enter to start, or 'q' to quit.")
    ask("  > ", valid=None, allow_quit=True)

    for task_key, image_id, technique, filepath in remaining:
        result = evaluate_workflow(image_id, technique, filepath, evaluator_name)

        if result is not None:
            completed.add(task_key)
            progress["completed"] = list(completed)
            save_progress(progress)

        done = len(completed)
        print(f"\n  Progress: {done}/{total} done")

        if done < total:
            cont = ask("\n  Continue to next? (y/n): ", valid=["y", "n"])
            if cont == "n":
                print("\n[*] Progress saved. Resume anytime by running this script again.")
                sys.exit(0)

    print("\n" + "=" * 62)
    print(f"  ALL DONE! Results saved to: {RESULTS_FILE}")
    print("=" * 62)


if __name__ == "__main__":
    main()