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


class TOTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    all_reasoning_process: str = Field("All the reasoning process from start to end, that lead to final decision about the plan")


output_parser = PydanticOutputParser(pydantic_object=TOTPrompt)


template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer using Tree of Thought reasoning.

GIVEN INFORMATION:
- Starting material: Solid cylindrical bar of cast iron
- Raw stock dimensions: 120 mm length, 60 mm diameter
- Available tools: Turning, Facing, Drilling, Chamfering, Step Turning, Taper Turning

Image details: {additional_text}
Image: {image}

Use Tree of Thought to explore multiple solution paths:

═══════════════════════════════════════════════════════════════
LEVEL 1: INITIAL PART ANALYSIS (Single Root)
═══════════════════════════════════════════════════════════════
Extract all features from the image:
- List all diameters with dimensions and positions
- List all special features (holes, tapers, chamfers)
- Note total part length

[Complete this analysis]

═══════════════════════════════════════════════════════════════
LEVEL 2: GENERATE 3 ALTERNATIVE MACHINING STRATEGIES (Branching)
═══════════════════════════════════════════════════════════════

BRANCH A: CONSERVATIVE APPROACH
Strategy: Minimize tool changes, maximize stability
- Start with facing both ends
- Rough turn entire length to near-largest required diameter
- Progressive step turning from largest to smallest
- Finish with holes, tapers, and chamfers
Estimated operations: ___
Risk level: LOW / MEDIUM / HIGH
Expected accuracy: ___

BRANCH B: FEATURE-PRIORITY APPROACH  
Strategy: Complete each diameter section fully before moving to next
- Face both ends
- Turn and finish first diameter section completely (including any holes/chamfers)
- Move to next diameter section, complete it fully
- Continue until all sections done
Estimated operations: ___
Risk level: LOW / MEDIUM / HIGH
Expected accuracy: ___

BRANCH C: EFFICIENCY-OPTIMIZED APPROACH
Strategy: Minimize material removal and operation count
- Face both ends
- Strategic turning to reduce overall material first
- Batch similar operations (all turning, then all drilling, then all chamfering)
- Minimize tool changes
Estimated operations: ___
Risk level: LOW / MEDIUM / HIGH
Expected accuracy: ___

[Generate all three branches with complete details]

═══════════════════════════════════════════════════════════════
LEVEL 3: EVALUATE EACH BRANCH (Scoring)
═══════════════════════════════════════════════════════════════

EVALUATION CRITERIA (Score each 0-10):

Branch A Scores:
- Efficiency (fewer operations): ___/10
- Safety (workpiece stability): ___/10  
- Accuracy (dimensional precision): ___/10
- Simplicity (ease of execution): ___/10
- Tool usage optimization: ___/10
TOTAL: ___/50
Key strengths: ___
Key weaknesses: ___

Branch B Scores:
- Efficiency: ___/10
- Safety: ___/10
- Accuracy: ___/10
- Simplicity: ___/10
- Tool usage: ___/10
TOTAL: ___/50
Key strengths: ___
Key weaknesses: ___

Branch C Scores:
- Efficiency: ___/10
- Safety: ___/10
- Accuracy: ___/10
- Simplicity: ___/10
- Tool usage: ___/10
TOTAL: ___/50
Key strengths: ___
Key weaknesses: ___

[Complete all evaluations with reasoning]

═══════════════════════════════════════════════════════════════
LEVEL 4: SELECT AND REFINE BEST BRANCH
═══════════════════════════════════════════════════════════════

Selected branch: ___ (highest score: ___/50)

Refinement process:
1. Take the selected branch's strategy
2. Incorporate the best elements from other branches:
   - From Branch ___: [specific technique/approach]
   - From Branch ___: [specific technique/approach]
3. Apply mandatory CNC rules:
   ✓ Facing both ends first
   ✓ Largest to smallest diameter progression
   ✓ Proper taper turning placement
   ✓ Chamfering on all sharp edges
   ✓ Optimal drilling operation placement

Refined strategy description:
[Detailed explanation of the optimized approach]

═══════════════════════════════════════════════════════════════
LEVEL 5: FINAL WORKFLOW GENERATION
═══════════════════════════════════════════════════════════════

Based on the refined strategy, generate the complete operation sequence:

Output Format: {format_instructions}

Generate the final workflow now.
""",
    input_variables=['image', 'additional_text'],
    partial_variables={'format_instructions': output_parser.get_format_instructions()}
)



def generate_tot_prompt(image_path: str, additional_text: str = "") -> str:
    """
    Convert the image to base64 and fill the prompt template with extra text.
    """
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64, additional_text=additional_text).to_string()
    return filled_prompt



def run_tot(image_path: str, image_details: str = ""):
    """
    Run the TOT workflow with context of the image using the model and parse the output.
    """
    model = load_model(model_name='gemini-2.5-pro')

    prompt_str = generate_tot_prompt(image_path=image_path, additional_text=image_details)

    raw_output = model.invoke(prompt_str)
    output_text = getattr(raw_output, 'content', str(raw_output))

    parsed_output = output_parser.parse(output_text)
    return parsed_output


if __name__ == "__main__":
    import json
    from src.workflow_1.image_understander.vlm_understander import run_vlm_for_image_understanding

    try:
        # image_path="data/curated_dataset/simple/simple_2.png"
        image_path="data/sample_images/tougher_sample.png"

        print("Running VLM to understand image.....")
        image_details = run_vlm_for_image_understanding(image_path=image_path)
        print(image_details)

        print("Generating workflow with image tot .....")
        result = run_tot(image_path=image_path, image_details=image_details)

        print(result)

    except Exception as e:
        print(f"Error!\nMessage: {e}")

    with open('temp/temp_tot_hard.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)
