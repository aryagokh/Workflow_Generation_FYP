import json
import re
import os
import warnings
from datetime import datetime

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

from src.utils import image_to_base64, load_model

warnings.filterwarnings(action="ignore")


# ── Schema ────────────────────────────────────────────────────────────────────

class Step(BaseModel):
    step_number: int = Field(..., description="Step number, starting from 1 and increasing sequentially")
    tool_name: str   = Field(..., description="Tool used in this step")
    tool_speed: str  = Field(..., description="Speed of the tool in RPM")
    description: str = Field(..., description="How the tool is used for manufacturing the part")


class TOTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    reasoning: str = Field(..., description="Full thought process from start to end, before making a manufacturing plan")
    step_by_step_plan: str = Field(..., description="Step by step plan of how to manufacture it from raw stock given to the end product, guide the laabours in very detail")


output_parser = PydanticOutputParser(pydantic_object=TOTPrompt)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    m = re.search(r"```json\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()


# ── Main function ─────────────────────────────────────────────────────────────

def run_tot(
    image_path: str,
    context_details: str = "",
    model_name: str = "gemini-3-flash-preview",
) -> TOTPrompt:

    model = load_model(model_name=model_name)

    img_b64 = image_to_base64(image_path)
    image_data_uri = f"data:image/png;base64,{img_b64}"

    instructions = f"""You are an expert CNC process planning engineer.

You are given an engineering drawing of a part that needs to be machined from a solid cylindrical cast iron bar of 150 mm length and 65 mm diameter. Your available tools are Turning, Facing, Drilling, Chamfering, Step Turning, and Taper Turning.

Additional context: {context_details}

Use Tree of Thought reasoning to arrive at the best manufacturing workflow. This means you should not commit to a single approach immediately — instead, explore multiple possible machining strategies, evaluate their trade-offs, and converge on the best one.

- Start by studying the drawing and identifying all features — diameters, lengths, holes, tapers, chamfers, and anything else visible.
- Then think of at least two or three distinct ways the part could be machined. These strategies might differ in how they sequence diameter reductions, when they perform drilling or chamfering, or how they handle complex features like tapers. For each strategy, think about what could go wrong — stability issues, operations that depend on surfaces not yet created, unnecessary tool changes, or dimensional inaccuracies.
- Once you have evaluated the alternatives, select the strongest approach and explain clearly why it is better than the others. If any strategy has a good idea that the chosen one lacks, incorporate it.
- Finally, use that refined strategy to generate the complete manufacturing workflow.

Capture the full exploration — all branches considered, their trade-offs, and your final decision — in the all_reasoning_process field.

{output_parser.get_format_instructions()}

Return ONLY valid JSON matching the schema above — no explanation, no markdown prose outside the JSON block.
"""

    message = HumanMessage(
        content=[
            {"type": "text",      "text": instructions},
            {"type": "image_url", "image_url": {"url": image_data_uri}},
        ]
    )

    print(f"[*] Sending multimodal TOT request to {model_name} ...")

    raw_output  = model.invoke([message])
    raw_content = getattr(raw_output, "content", str(raw_output))

    if isinstance(raw_content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )
    else:
        content = raw_content

    print("[*] Raw model output received. Parsing ...")

    clean_json = _extract_json(content)
    parsed: TOTPrompt = output_parser.parse(clean_json)

    return parsed


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    image_path = "data/curated_dataset/hard/hard_5.png"
    context    = "Analyze for Step Turning, Tapering, Grooving and other features."

    try:
        result = run_tot(
            image_path=image_path,
            context_details=context,
        )

        print("\n--- AI-Generated TOT Manufacturing Workflow ---")
        print(json.dumps(result.model_dump(), indent=4))

        output_dir = os.path.join("output", "tot_results")
        os.makedirs(output_dir, exist_ok=True)

        timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
        name        = 'hard_5'
        output_path = os.path.join(output_dir, f"result_{name}_{timestamp}.json")

        with open(output_path, "w") as f:
            json.dump(result.model_dump(), f, indent=4)

        print(f"\n[*] Result saved to: {output_path}")

    except Exception as e:
        print(f"Pipeline Error: {e}")
        raise