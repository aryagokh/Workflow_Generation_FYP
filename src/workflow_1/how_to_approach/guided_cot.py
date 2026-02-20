from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import List
from src.utils import image_to_base64, load_model
import warnings

warnings.filterwarnings(action='ignore')

class Step(BaseModel):
    step_number: int = Field(..., description="Step number, starting from 1 and increasing sequentially")
    tool_name: str = Field(..., description="Tool used in this step")
    tool_speed: str = Field(..., description="Speed of the tool in RPM")
    description: str = Field(..., description="How the tool is used for manufacturing the part")


class GuidedCOTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    all_reasoning_process: str = Field("All the reasoning process from start to end, that lead to final decision about the plan")


output_parser = PydanticOutputParser(pydantic_object=GuidedCOTPrompt)


template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer.

GIVEN INFORMATION:
- Starting material: Solid cylindrical bar of cast iron
- Raw stock dimensions: 120 mm length, 60 mm diameter
- Available tools: Turning, Facing, Drilling, Chamfering, Step Turning, Taper Turning

Image details: {additional_text}
Image: {image}

Follow this EXACT reasoning process and show your work at each step:

═══════════════════════════════════════════════════════════════
STEP 1: PART FEATURE EXTRACTION
═══════════════════════════════════════════════════════════════
Analyze the image and extract:

1a) List ALL diameter sections from the image:
    - Diameter 1: ___ mm, Location: ___, Length: ___ mm
    - Diameter 2: ___ mm, Location: ___, Length: ___ mm
    [Continue for all diameters]

1b) List ALL special features:
    - Holes: [diameter, depth, location]
    - Tapers: [start diameter, end diameter, length, location]
    - Chamfers: [location, angle/size]
    - Threads: [if any]

1c) Total part length required: ___ mm

[COMPLETE STEP 1 BEFORE PROCEEDING]

═══════════════════════════════════════════════════════════════
STEP 2: DIAMETER SEQUENCING
═══════════════════════════════════════════════════════════════
Order all diameters from LARGEST to SMALLEST:

Raw stock: 60 mm
↓
Target diameter 1: ___ mm (reduction of ___ mm)
↓
Target diameter 2: ___ mm (reduction of ___ mm)
↓
Target diameter 3: ___ mm (reduction of ___ mm)
[Continue sequence]

Reasoning for this sequence:
[Explain why this order is correct for CNC machining]

[COMPLETE STEP 2 BEFORE PROCEEDING]

═══════════════════════════════════════════════════════════════
STEP 3: OPERATION MAPPING
═══════════════════════════════════════════════════════════════
For each diameter and feature, determine the required operation:

Operation 1: FACING (Left end)
- Purpose: Create reference surface
- Tool: Facing tool
- Target: Flat surface perpendicular to axis

Operation 2: FACING (Right end)
- Purpose: Establish final length at ___ mm
- Tool: Facing tool
- Target: Flat surface, total length = ___ mm

Operation 3: TURNING (First diameter reduction)
- Purpose: Reduce from 60 mm to ___ mm
- Tool: Turning tool
- Length affected: ___ mm (from position ___ to ___)
- Material removed: ___ mm radius

[Continue mapping for ALL features identified in Step 1]

[COMPLETE STEP 3 BEFORE PROCEEDING]

═══════════════════════════════════════════════════════════════
STEP 4: DEPENDENCY VALIDATION
═══════════════════════════════════════════════════════════════
Check each operation's dependencies:

For Operation 3 (First turning):
- Requires: Operations 1 & 2 completed ✓
- Reason: Need reference surfaces first

For Operation 4 (Step turning to next diameter):
- Requires: Operation 3 completed ✓
- Reason: Must machine larger diameter before smaller

[Check ALL operations]

Identify any conflicts or ordering issues:
[List any problems found and how to resolve them]

[COMPLETE STEP 4 BEFORE PROCEEDING]

═══════════════════════════════════════════════════════════════
STEP 5: SAFETY AND QUALITY CHECKS
═══════════════════════════════════════════════════════════════
Verify the following:

✓ All sharp external edges have chamfering operations planned
✓ Workpiece remains stable throughout all operations
✓ No operation creates undercuts that prevent subsequent operations
✓ Drilling operations occur when access is clear
✓ All dimensions from the image are accounted for

Issues found: [None / List issues]
Corrections needed: [None / List corrections]

[COMPLETE STEP 5 BEFORE PROCEEDING]

═══════════════════════════════════════════════════════════════
STEP 6: FINAL WORKFLOW GENERATION
═══════════════════════════════════════════════════════════════
Based on Steps 1-5, present the complete workflow:

Output Format: {format_instructions}

Generate the final workflow now.
""",
    input_variables=['image', 'additional_text'],
    partial_variables={'format_instructions': output_parser.get_format_instructions()}
)



def generate_guided_cot_prompt(image_path: str, additional_text: str = "") -> str:
    """
    Convert the image to base64 and fill the prompt template with extra text.
    """
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64, additional_text=additional_text).to_string()
    return filled_prompt



def run_guided_cot(image_path: str, image_details: str = ""):
    """
    Run the Guided COT workflow with context of the image using the model and parse the output.
    """
    model = load_model(model_name='gemini-2.5-pro')

    prompt_str = generate_guided_cot_prompt(image_path=image_path, additional_text=image_details)

    raw_output = model.invoke(prompt_str)
    output_text = getattr(raw_output, 'content', str(raw_output))

    parsed_output = output_parser.parse(output_text)
    return parsed_output


if __name__ == "__main__":
    import json
    from src.workflow_1.image_understander.vlm_understander import run_vlm_for_image_understanding

    try:
        image_path="data/curated_dataset/simple/simple_2.png"

        print("Running VLM to understand image.....")
        image_details = run_vlm_for_image_understanding(image_path=image_path)
        print(image_details)

        print("Generating workflow with image aware guided cot .....")
        result = run_guided_cot(image_path=image_path, image_details=image_details)

        print(result)

    except Exception as e:
        print(f"Error!\nMessage: {e}")

    with open('temp/temp_guided_cot.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)
