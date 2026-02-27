# """
# CNC Workflow Evaluator — Terminal Tool
# Run: python evaluator.py

# Evaluates JSON workflow outputs using WFS, FRS, ROAS, ORR metrics.
# Saves progress to a central file and supports resume + quit.
# """

# import json
# import os
# import sys
# import glob
# from datetime import datetime

# PROGRESS_FILE = "output/evaluation_progress.json"
# RESULTS_FILE  = "output/evaluation_results.json"

# TECHNIQUES = ["zero_shot", "cot", "guided_cot", "tot", "got"]
# CATEGORIES = ["simple", "medium", "hard"]

# HAS_REASONING = {"cot", "guided_cot", "tot", "got"}


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
#     # Update if already exists, else append
#     key = (result["image_id"], result["technique"])
#     for i, r in enumerate(results):
#         if r["image_id"] == result["image_id"] and r["technique"] == result["technique"]:
#             results[i] = result
#             save_json(RESULTS_FILE, results)
#             return
#     results.append(result)
#     save_json(RESULTS_FILE, results)

# def get_result_files(technique, category):
#     folder = f"output/{technique}_results"
#     pattern = os.path.join(folder, f"result_{category}_*.json")
#     files = sorted(glob.glob(pattern))
#     return files

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

# def ask_float(prompt):
#     while True:
#         val = input(prompt).strip()
#         if val.lower() == "q":
#             print("\n[*] Progress saved. Exiting.")
#             sys.exit(0)
#         try:
#             f = float(val)
#             if 0.0 <= f <= 1.0:
#                 return round(f, 4)
#             print("    Enter a value between 0.0 and 1.0")
#         except ValueError:
#             print("    Invalid number. Try again.")

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


# # ── Compute WQI ───────────────────────────────────────────────────────────────

# def compute_wqi(wfs, frs, roas, orr, has_reasoning):
#     one_minus_orr = 1 - orr
#     if has_reasoning and roas is not None:
#         wqi = 0.35 * wfs + 0.30 * frs + 0.20 * roas + 0.15 * one_minus_orr
#     else:
#         wqi = 0.41 * wfs + 0.35 * frs + 0.24 * one_minus_orr
#     return round(wqi, 4)


# # ── Evaluate one workflow ──────────────────────────────────────────────────────

# def evaluate_workflow(image_id, technique, filepath, evaluator_name):
#     print(f"\n{'='*60}")
#     print(f"  Image  : {image_id}")
#     print(f"  File   : {filepath}")
#     print(f"{'='*60}")
#     print("  (Technique hidden for blind evaluation)")

#     try:
#         data = load_json(filepath)
#         steps = data.get("steps", [])
#         total_steps = len(steps)

#         print(f"\n  Total steps: {total_steps}")
#         print(f"\n  {chr(8212)*56}")
#         print("  STEPS:")
#         print(f"  {chr(8212)*56}")
#         for s in steps:
#             print(f"\n  Step {s['step_number']}: {s['tool_name']} @ {s.get('tool_speed', 'N/A')}")
#             print(f"  {s['description']}")

#         reasoning = data.get("all_reasoning_process", None) or data.get("reasoning", None)
#         if reasoning:
#             print(f"\n  {chr(8212)*56}")
#             print("  REASONING PROCESS:")
#             print(f"  {chr(8212)*56}")
#             words = reasoning.split()
#             line = "  "
#             for word in words:
#                 if len(line) + len(word) + 1 > 72:
#                     print(line)
#                     line = "  " + word + " "
#                 else:
#                     line += word + " "
#             if line.strip():
#                 print(line)

#         plan = data.get("step_by_step_plan", None)
#         if plan:
#             print(f"\n  {chr(8212)*56}")
#             print("  STEP BY STEP PLAN:")
#             print(f"  {chr(8212)*56}")
#             for pl in plan.split("\n"):
#                 print(f"  {pl.strip()}")

#         print(f"\n  {chr(8212)*56}")

#     except Exception as e:
#         print(f"  Could not load file: {e}")
#         return None

#     print(f"\n{'─'*60}")
#     print("  Type 'q' at any prompt to save and quit.\n")

#     # WFS
#     print("  [METRIC 1] Workflow Feasibility Score (WFS)")
#     print("  How many dependency violations did you find?")
#     print("  (e.g. turning before facing, smaller diameter before larger)")
#     violations = ask_int("  Violations (V): ", min_val=0)
#     wfs = round(1 - (violations / total_steps), 4) if total_steps > 0 else 0.0
#     print(f"  → WFS = 1 - ({violations}/{total_steps}) = {wfs}")

#     # FRS
#     print("\n  [METRIC 2] Feature Recall Score (FRS)")
#     total_features = ask_int("  Total features in drawing: ", min_val=1)
#     addressed      = ask_int("  Features addressed by workflow: ", min_val=0)
#     frs = round(addressed / total_features, 4) if total_features > 0 else 0.0
#     print(f"  → FRS = {addressed}/{total_features} = {frs}")

#     # ROAS
#     roas = None
#     if technique in HAS_REASONING:
#         print("\n  [METRIC 3] Reasoning-Output Alignment Score (ROAS)")
#         print("  How many steps have explicit, concrete justification in the reasoning field?")
#         justified = ask_int("  Justified steps: ", min_val=0)
#         roas = round(justified / total_steps, 4) if total_steps > 0 else 0.0
#         print(f"  → ROAS = {justified}/{total_steps} = {roas}")
#     else:
#         print("\n  [METRIC 3] ROAS — N/A (Zero-Shot has no reasoning field)")

#     # ORR
#     print("\n  [METRIC 4] Operational Redundancy Rate (ORR)")
#     print("  How many steps are redundant or repeated?")
#     redundant = ask_int("  Redundant steps: ", min_val=0)
#     orr = round(redundant / total_steps, 4) if total_steps > 0 else 0.0
#     print(f"  → ORR = {redundant}/{total_steps} = {orr}")
#     print(f"  → (1 - ORR) = {round(1-orr, 4)}")

#     # WQI
#     wqi = compute_wqi(wfs, frs, roas, orr, technique in HAS_REASONING)
#     print(f"\n  {'─'*40}")
#     print(f"  ✓ WQI = {wqi}")
#     print(f"  {'─'*40}")

#     # Notes
#     notes = input("\n  Any observations? (press Enter to skip): ").strip()

#     result = {
#         "image_id"      : image_id,
#         "technique"     : technique,
#         "evaluator"     : evaluator_name,
#         "file"          : filepath,
#         "timestamp"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "total_steps"   : total_steps,
#         "violations"    : violations,
#         "wfs"           : wfs,
#         "total_features": total_features,
#         "addressed"     : addressed,
#         "frs"           : frs,
#         "roas"          : roas,
#         "redundant"     : redundant,
#         "orr"           : orr,
#         "wqi"           : wqi,
#         "notes"         : notes
#     }

#     save_result(result)
#     print(f"\n  [*] Saved to {RESULTS_FILE}")
#     return result


# # ── Main ──────────────────────────────────────────────────────────────────────

# def main():
#     print("\n" + "="*60)
#     print("   CNC WORKFLOW EVALUATOR")
#     print("="*60)
#     print("  Type 'q' at any prompt to save progress and quit.\n")

#     progress = load_progress()

#     # Get or confirm evaluator name
#     if progress["evaluator_name"]:
#         print(f"  Welcome back, {progress['evaluator_name']}!")
#         change = ask("  Continue as same evaluator? (y/n): ", valid=["y", "n"])
#         if change == "n":
#             progress["evaluator_name"] = None

#     if not progress["evaluator_name"]:
#         name = input("  Enter your name: ").strip()
#         if not name:
#             name = "Evaluator"
#         progress["evaluator_name"] = name
#         save_progress(progress)

#     evaluator_name = progress["evaluator_name"]
#     completed      = set(progress["completed"])

#     # Build task list — grouped by image, techniques shuffled per image (blind eval)
#     import random
#     tasks = []
#     # Group by image_id first, then shuffle techniques within each image
#     image_tasks = {}  # image_id -> list of (task_key, image_id, technique, filepath)
#     for technique in TECHNIQUES:
#         for category in CATEGORIES:
#             files = get_result_files(technique, category)
#             for filepath in files:
#                 basename = os.path.basename(filepath)
#                 parts    = basename.replace("result_", "").split("_")
#                 image_id = f"{parts[0]}_{parts[1]}"  # e.g. simple_1
#                 task_key = f"{image_id}__{technique}"
#                 if image_id not in image_tasks:
#                     image_tasks[image_id] = []
#                 image_tasks[image_id].append((task_key, image_id, technique, filepath))

#     # For each image, shuffle the technique order (blind evaluation)
#     # Use a fixed seed per evaluator so order is consistent on resume
#     seed = sum(ord(c) for c in evaluator_name)
#     rng  = random.Random(seed)
#     # Sort by category order (simple → medium → hard), then by number
#     def sort_key(img_id):
#         cat = img_id.split("_")[0]
#         num = img_id.split("_")[1]
#         order = {"simple": 0, "medium": 1, "hard": 2}
#         return (order.get(cat, 99), int(num))

#     for image_id in sorted(image_tasks.keys(), key=sort_key):
#         group = image_tasks[image_id]
#         rng.shuffle(group)
#         tasks.extend(group)

#     remaining = [t for t in tasks if t[0] not in completed]
#     total     = len(tasks)
#     done      = len(completed)

#     print(f"\n  Progress: {done}/{total} evaluations completed")

#     if not remaining:
#         print("\n  All evaluations complete!")
#         print(f"  Results saved in: {RESULTS_FILE}")
#         return

#     print(f"  Remaining: {len(remaining)}")
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

#     print("\n" + "="*60)
#     print(f"  ALL DONE! Results saved to: {RESULTS_FILE}")
#     print("="*60)


# if __name__ == "__main__":
#     main()

# ---------------------------------------------------------------------------------

# """
# CNC Workflow Evaluator — Terminal Tool
# Run: python evaluator.py

# Evaluates JSON workflow outputs using WFS, FRS, ROAS, ORR metrics.
# Saves progress to a central file and supports resume + quit.
# """

# import json
# import os
# import sys
# import glob
# from datetime import datetime

# PROGRESS_FILE = "output/evaluation_progress.json"
# RESULTS_FILE  = "output/evaluation_results.json"

# TECHNIQUES = ["zero_shot", "cot", "guided_cot", "tot", "got"]
# CATEGORIES = ["simple", "medium", "hard"]

# HAS_REASONING = {"cot", "guided_cot", "tot", "got"}


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
#     # Update if already exists, else append
#     key = (result["image_id"], result["technique"])
#     for i, r in enumerate(results):
#         if r["image_id"] == result["image_id"] and r["technique"] == result["technique"]:
#             results[i] = result
#             save_json(RESULTS_FILE, results)
#             return
#     results.append(result)
#     save_json(RESULTS_FILE, results)

# def get_result_files(technique, category):
#     folder = f"output/{technique}_results"
#     pattern = os.path.join(folder, f"result_{category}_*.json")
#     files = sorted(glob.glob(pattern))
#     return files

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

# def ask_float(prompt):
#     while True:
#         val = input(prompt).strip()
#         if val.lower() == "q":
#             print("\n[*] Progress saved. Exiting.")
#             sys.exit(0)
#         try:
#             f = float(val)
#             if 0.0 <= f <= 1.0:
#                 return round(f, 4)
#             print("    Enter a value between 0.0 and 1.0")
#         except ValueError:
#             print("    Invalid number. Try again.")

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


# # ── Compute WQI ───────────────────────────────────────────────────────────────

# def compute_wqi(wfs, frs, roas, orr, has_reasoning):
#     one_minus_orr = 1 - orr
#     if has_reasoning and roas is not None:
#         wqi = 0.35 * wfs + 0.30 * frs + 0.20 * roas + 0.15 * one_minus_orr
#     else:
#         wqi = 0.41 * wfs + 0.35 * frs + 0.24 * one_minus_orr
#     return round(wqi, 4)


# # ── Evaluate one workflow ──────────────────────────────────────────────────────

# def evaluate_workflow(image_id, technique, filepath, evaluator_name):
#     print(f"\n{'='*60}")
#     print(f"  Image  : {image_id}")
#     print(f"  File   : {filepath}")
#     print(f"{'='*60}")
#     print("  (Technique hidden for blind evaluation)")

#     try:
#         data = load_json(filepath)
#         steps = data.get("steps", [])
#         total_steps = len(steps)

#         print(f"\n  Total steps: {total_steps}")
#         print(f"\n  {chr(8212)*56}")
#         print("  STEPS:")
#         print(f"  {chr(8212)*56}")
#         for s in steps:
#             print(f"\n  Step {s['step_number']}: {s['tool_name']} @ {s.get('tool_speed', 'N/A')}")
#             print(f"  {s['description']}")

#         reasoning = data.get("all_reasoning_process", None) or data.get("reasoning", None)
#         if reasoning:
#             print(f"\n  {chr(8212)*56}")
#             print("  REASONING PROCESS:")
#             print(f"  {chr(8212)*56}")
#             words = reasoning.split()
#             line = "  "
#             for word in words:
#                 if len(line) + len(word) + 1 > 72:
#                     print(line)
#                     line = "  " + word + " "
#                 else:
#                     line += word + " "
#             if line.strip():
#                 print(line)

#         plan = data.get("step_by_step_plan", None)
#         if plan:
#             print(f"\n  {chr(8212)*56}")
#             print("  STEP BY STEP PLAN:")
#             print(f"  {chr(8212)*56}")
#             for pl in plan.split("\n"):
#                 print(f"  {pl.strip()}")

#         print(f"\n  {chr(8212)*56}")

#     except Exception as e:
#         print(f"  Could not load file: {e}")
#         return None

#     print(f"\n{'─'*60}")
#     print("  Type 'q' at any prompt to save and quit.\n")

#     # WFS
#     print("  [METRIC 1] Workflow Feasibility Score (WFS)")
#     print("  How many dependency violations did you find?")
#     print("  (e.g. turning before facing, smaller diameter before larger)")
#     violations = ask_int("  Violations (V): ", min_val=0)
#     wfs = round(1 - (violations / total_steps), 4) if total_steps > 0 else 0.0
#     print(f"  → WFS = 1 - ({violations}/{total_steps}) = {wfs}")

#     # FRS
#     print("\n  [METRIC 2] Feature Recall Score (FRS)")
#     total_features = ask_int("  Total features in drawing: ", min_val=1)
#     addressed      = ask_int("  Features addressed by workflow: ", min_val=0)
#     frs = round(addressed / total_features, 4) if total_features > 0 else 0.0
#     print(f"  → FRS = {addressed}/{total_features} = {frs}")

#     # ROAS
#     roas = None
#     if technique in HAS_REASONING:
#         print("\n  [METRIC 3] Reasoning-Output Alignment Score (ROAS)")
#         print("  How many steps have explicit, concrete justification in the reasoning field?")
#         justified = ask_int("  Justified steps: ", min_val=0)
#         roas = round(justified / total_steps, 4) if total_steps > 0 else 0.0
#         print(f"  → ROAS = {justified}/{total_steps} = {roas}")
#     else:
#         print("\n  [METRIC 3] ROAS — N/A (Zero-Shot has no reasoning field)")

#     # ORR
#     print("\n  [METRIC 4] Operational Redundancy Rate (ORR)")
#     print("  How many steps are redundant or repeated?")
#     redundant = ask_int("  Redundant steps: ", min_val=0)
#     orr = round(redundant / total_steps, 4) if total_steps > 0 else 0.0
#     print(f"  → ORR = {redundant}/{total_steps} = {orr}")
#     print(f"  → (1 - ORR) = {round(1-orr, 4)}")

#     # WQI
#     wqi = compute_wqi(wfs, frs, roas, orr, technique in HAS_REASONING)
#     print(f"\n  {'─'*40}")
#     print(f"  ✓ WQI = {wqi}")
#     print(f"  {'─'*40}")

#     # Notes
#     notes = input("\n  Any observations? (press Enter to skip): ").strip()

#     result = {
#         "image_id"      : image_id,
#         "technique"     : technique,
#         "evaluator"     : evaluator_name,
#         "file"          : filepath,
#         "timestamp"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "total_steps"   : total_steps,
#         "violations"    : violations,
#         "wfs"           : wfs,
#         "total_features": total_features,
#         "addressed"     : addressed,
#         "frs"           : frs,
#         "roas"          : roas,
#         "redundant"     : redundant,
#         "orr"           : orr,
#         "wqi"           : wqi,
#         "notes"         : notes
#     }

#     save_result(result)
#     print(f"\n  [*] Saved to {RESULTS_FILE}")
#     return result


# # ── Main ──────────────────────────────────────────────────────────────────────

# def main():
#     print("\n" + "="*60)
#     print("   CNC WORKFLOW EVALUATOR")
#     print("="*60)
#     print("  Type 'q' at any prompt to save progress and quit.\n")

#     progress = load_progress()

#     # Get or confirm evaluator name
#     if progress["evaluator_name"]:
#         print(f"  Welcome back, {progress['evaluator_name']}!")
#         change = ask("  Continue as same evaluator? (y/n): ", valid=["y", "n"])
#         if change == "n":
#             progress["evaluator_name"] = None

#     if not progress["evaluator_name"]:
#         name = input("  Enter your name: ").strip()
#         if not name:
#             name = "Evaluator"
#         progress["evaluator_name"] = name
#         save_progress(progress)

#     evaluator_name = progress["evaluator_name"]
#     completed      = set(progress["completed"])

#     # Build task list — simple_1 (all techniques) → simple_2 → ... → hard_5
#     # First collect all image_ids per category in order
#     import re
#     image_map = {}  # image_id -> {technique: filepath}
#     for technique in TECHNIQUES:
#         for category in CATEGORIES:
#             files = get_result_files(technique, category)
#             for filepath in files:
#                 basename = os.path.basename(filepath)
#                 parts    = basename.replace("result_", "").split("_")
#                 image_id = f"{parts[0]}_{parts[1]}"
#                 if image_id not in image_map:
#                     image_map[image_id] = {}
#                 image_map[image_id][technique] = filepath

#     # Sort images: simple→medium→hard, then by number
#     def image_sort_key(img_id):
#         cat = img_id.split("_")[0]
#         num = img_id.split("_")[1]
#         order = {"simple": 0, "medium": 1, "hard": 2}
#         return (order.get(cat, 99), int(num))

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

#     print(f"\n  Progress: {done}/{total} evaluations completed")

#     if not remaining:
#         print("\n  All evaluations complete!")
#         print(f"  Results saved in: {RESULTS_FILE}")
#         return

#     print(f"  Remaining: {len(remaining)}")
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

#     print("\n" + "="*60)
#     print(f"  ALL DONE! Results saved to: {RESULTS_FILE}")
#     print("="*60)


# if __name__ == "__main__":
#     main()

"""
CNC Workflow Evaluator — Terminal Tool
Run: python evaluator.py

Evaluates JSON workflow outputs using WFS, FRS, ROAS, ORR metrics.
Saves progress to a central file and supports resume + quit.
"""

import json
import os
import sys
import glob
from datetime import datetime

PROGRESS_FILE = "output/evaluation_progress.json"
RESULTS_FILE  = "output/evaluation_results.json"

TECHNIQUES = ["zero_shot", "cot", "guided_cot", "tot", "got"]
CATEGORIES = ["simple", "medium", "hard"]

HAS_REASONING = {"cot", "guided_cot", "tot", "got"}


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
    # Update if already exists, else append
    key = (result["image_id"], result["technique"])
    for i, r in enumerate(results):
        if r["image_id"] == result["image_id"] and r["technique"] == result["technique"]:
            results[i] = result
            save_json(RESULTS_FILE, results)
            return
    results.append(result)
    save_json(RESULTS_FILE, results)

def get_result_files(technique, category):
    folder = f"output/{technique}_results"
    pattern = os.path.join(folder, f"result_{category}_*.json")
    files = sorted(glob.glob(pattern))
    return files

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

def ask_float(prompt):
    while True:
        val = input(prompt).strip()
        if val.lower() == "q":
            print("\n[*] Progress saved. Exiting.")
            sys.exit(0)
        try:
            f = float(val)
            if 0.0 <= f <= 1.0:
                return round(f, 4)
            print("    Enter a value between 0.0 and 1.0")
        except ValueError:
            print("    Invalid number. Try again.")

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


# ── Compute WQI ───────────────────────────────────────────────────────────────

def compute_wqi(wfs, frs, roas, orr, has_reasoning):
    one_minus_orr = 1 - orr
    if has_reasoning and roas is not None:
        wqi = 0.35 * wfs + 0.30 * frs + 0.20 * roas + 0.15 * one_minus_orr
    else:
        wqi = 0.41 * wfs + 0.35 * frs + 0.24 * one_minus_orr
    return round(wqi, 4)


# ── Evaluate one workflow ──────────────────────────────────────────────────────

def evaluate_workflow(image_id, technique, filepath, evaluator_name):
    print(f"\n{'='*60}")
    print(f"  Image  : {image_id}")
    print(f"  File   : {filepath}")
    print(f"{'='*60}")
    print("  (Technique hidden for blind evaluation)")

    try:
        data = load_json(filepath)
        steps = data.get("steps", [])
        total_steps = len(steps)

        print(f"\n  Total steps: {total_steps}")
        print(f"\n  {chr(8212)*56}")
        print("  STEPS:")
        print(f"  {chr(8212)*56}")
        for s in steps:
            print(f"\n  Step {s['step_number']}: {s['tool_name']} @ {s.get('tool_speed', 'N/A')}")
            print(f"  {s['description']}")

        reasoning = data.get("all_reasoning_process", None) or data.get("reasoning", None)
        if reasoning:
            print(f"\n  {chr(8212)*56}")
            print("  REASONING PROCESS (read this to score ROAS):")
            print(f"  {chr(8212)*56}")
            # Word wrap reasoning as plain text
            words = reasoning.split()
            line  = "  "
            for word in words:
                if len(line) + len(word) + 1 > 72:
                    print(line)
                    line = "  " + word + " "
                else:
                    line += word + " "
            if line.strip():
                print(line)

        plan = data.get("step_by_step_plan", None)
        if plan:
            print(f"\n  {chr(8212)*56}")
            print("  STEP BY STEP PLAN:")
            print(f"  {chr(8212)*56}")
            for pl in plan.split("\n"):
                print(f"  {pl.strip()}")

        print(f"\n  {chr(8212)*56}")

    except Exception as e:
        print(f"  Could not load file: {e}")
        return None

    print(f"\n{'─'*60}")
    print("  Type 'q' at any prompt to save and quit.\n")

    # Orientation check
    print("  [ORIENTATION CHECK]")
    print("  Is the overall machining orientation and setup correct?")
    print("    1 = Yes, fully correct")
    print("    2 = Orientation wrong but step logic is valid")
    print("    0 = Completely wrong, unusable")
    orientation = ask("  Enter (0/1/2): ", valid=["0", "1", "2"])
    multipliers = {"1": 1.0, "2": 0.5, "0": 0.0}
    orientation_weight = multipliers[orientation]
    print(f"  → Orientation weight: {orientation_weight}")

    # WFS
    print("  [METRIC 1] Workflow Feasibility Score (WFS)")
    print("  How many dependency violations did you find?")
    print("  (e.g. turning before facing, smaller diameter before larger)")
    violations = ask_int("  Violations (V): ", min_val=0)
    wfs = round(1 - (violations / total_steps), 4) if total_steps > 0 else 0.0
    print(f"  → WFS = 1 - ({violations}/{total_steps}) = {wfs}")

    # FRS
    print("\n  [METRIC 2] Feature Recall Score (FRS)")
    total_features = ask_int("  Total features in drawing: ", min_val=1)
    addressed      = ask_int("  Features addressed by workflow: ", min_val=0)
    frs = round(addressed / total_features, 4) if total_features > 0 else 0.0
    print(f"  → FRS = {addressed}/{total_features} = {frs}")

    # ROAS
    roas = None
    if technique in HAS_REASONING:
        print("\n  [METRIC 3] Reasoning-Output Alignment Score (ROAS)")
        print("  How many steps have explicit, concrete justification in the reasoning field?")
        justified = ask_int("  Justified steps: ", min_val=0)
        roas = round(justified / total_steps, 4) if total_steps > 0 else 0.0
        print(f"  → ROAS = {justified}/{total_steps} = {roas}")
    else:
        print("\n  [METRIC 3] ROAS — N/A (Zero-Shot has no reasoning field)")

    # ORR
    print("\n  [METRIC 4] Operational Redundancy Rate (ORR)")
    print("  How many steps are redundant or repeated?")
    redundant = ask_int("  Redundant steps: ", min_val=0)
    orr = round(redundant / total_steps, 4) if total_steps > 0 else 0.0
    print(f"  → ORR = {redundant}/{total_steps} = {orr}")
    print(f"  → (1 - ORR) = {round(1-orr, 4)}")

    # WQI
    wqi = compute_wqi(wfs, frs, roas, orr, technique in HAS_REASONING)
    wqi = round(wqi * orientation_weight, 4)
    print(f"\n  {'─'*40}")
    print(f"  ✓ WQI = {wqi} (× {orientation_weight} orientation weight)")
    print(f"  {'─'*40}")

    # Notes
    notes = input("\n  Any observations? (press Enter to skip): ").strip()

    result = {
        "image_id"           : image_id,
        "technique"          : technique,
        "evaluator"          : evaluator_name,
        "file"               : filepath,
        "timestamp"          : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_steps"        : total_steps,
        "orientation_weight" : orientation_weight,
        "violations"         : violations,
        "wfs"                : wfs,
        "total_features"     : total_features,
        "addressed"          : addressed,
        "frs"                : frs,
        "roas"               : roas,
        "redundant"          : redundant,
        "orr"                : orr,
        "wqi"                : wqi,
        "notes"              : notes
    }

    save_result(result)
    print(f"\n  [*] Saved to {RESULTS_FILE}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("   CNC WORKFLOW EVALUATOR")
    print("="*60)
    print("  Type 'q' at any prompt to save progress and quit.\n")

    progress = load_progress()

    # Get or confirm evaluator name
    if progress["evaluator_name"]:
        print(f"  Welcome back, {progress['evaluator_name']}!")
        change = ask("  Continue as same evaluator? (y/n): ", valid=["y", "n"])
        if change == "n":
            progress["evaluator_name"] = None

    if not progress["evaluator_name"]:
        name = input("  Enter your name: ").strip()
        if not name:
            name = "Evaluator"
        progress["evaluator_name"] = name
        save_progress(progress)

    evaluator_name = progress["evaluator_name"]
    completed      = set(progress["completed"])

    # Build task list — simple_1 (all techniques) → simple_2 → ... → hard_5
    # First collect all image_ids per category in order
    import re
    image_map = {}  # image_id -> {technique: filepath}
    for technique in TECHNIQUES:
        for category in CATEGORIES:
            files = get_result_files(technique, category)
            for filepath in files:
                basename = os.path.basename(filepath)
                parts    = basename.replace("result_", "").split("_")
                image_id = f"{parts[0]}_{parts[1]}"
                if image_id not in image_map:
                    image_map[image_id] = {}
                image_map[image_id][technique] = filepath

    # Sort images: simple_1→medium_1→hard_1→simple_2→medium_2→hard_2...
    def image_sort_key(img_id):
        cat = img_id.split("_")[0]
        num = img_id.split("_")[1]
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

    print(f"\n  Progress: {done}/{total} evaluations completed")

    if not remaining:
        print("\n  All evaluations complete!")
        print(f"  Results saved in: {RESULTS_FILE}")
        return

    print(f"  Remaining: {len(remaining)}")
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

    print("\n" + "="*60)
    print(f"  ALL DONE! Results saved to: {RESULTS_FILE}")
    print("="*60)


# Yes — what you're describing is essentially measuring how much the reasoning structure actually helped compared to just guessing. I'd call it:

# Reasoning Guidance Score (RGS)
# The idea: compare WQI of a reasoning technique against zero-shot on the same image. If the technique genuinely guided the model better, its WQI should be higher.
# RGS = (WQI_technique - WQI_zeroshot) / WQI_zeroshot
# Positive RGS → technique guided better than zero-shot
# Zero RGS → no improvement over zero-shot
# Negative RGS → technique actually confused the model, performed worse
# Example:
# On hard_1:

# Zero-shot WQI = 0.60
# GOT WQI = 0.85

# RGS = (0.85 - 0.60) / 0.60 = +0.417 → GOT guided 41.7% better
# On the same image:

# COT WQI = 0.58

# RGS = (0.58 - 0.60) / 0.60 = -0.033 → COT slightly confused, performed marginally worse than zero-shot

if __name__ == "__main__":
    main()