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


class GOTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    all_reasoning_process: str = Field("All the reasoning process from start to end, that lead to final decision about the plan")


output_parser = PydanticOutputParser(pydantic_object=GOTPrompt)

template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer using Graph of Thought reasoning.

GIVEN INFORMATION:
- Starting material: Solid cylindrical bar of cast iron
- Raw stock dimensions: 120 mm length, 60 mm diameter
- Available tools: Turning, Facing, Drilling, Chamfering, Step Turning, Taper Turning

Image details: {additional_text}
Image: {image}

Build a reasoning graph where nodes are thoughts/operations and edges are dependencies:

═══════════════════════════════════════════════════════════════
GRAPH LAYER 0: FEATURE IDENTIFICATION NODES
═══════════════════════════════════════════════════════════════

Create nodes for each feature identified in the image:

NODE-F1: [Feature type: Diameter/Hole/Taper/Chamfer]
  Properties: {{dimension: ___, position: ___, length: ___}}
  
NODE-F2: [Feature type: ___]
  Properties: {{dimension: ___, position: ___, length: ___}}

[Create nodes for ALL features]

Node connections at this layer: [Describe spatial relationships]

═══════════════════════════════════════════════════════════════
GRAPH LAYER 1: OPERATION NODES (Initial Set)
═══════════════════════════════════════════════════════════════

Map each feature to required operation(s):

NODE-OP0: "Initial State"
  Properties: {{diameter: 60mm, length: 120mm, material: cast_iron}}
  Connects to: [all first operations]

NODE-OP1: "Face Left End"
  Properties: {{tool: facing, purpose: reference_surface}}
  Input edges from: NODE-OP0
  Output edges to: [nodes that need reference surface]

NODE-OP2: "Face Right End"  
  Properties: {{tool: facing, purpose: establish_length, target: ___mm}}
  Input edges from: NODE-OP0
  Output edges to: [nodes that need final length established]

NODE-OP3: "Turn to First Diameter"
  Properties: {{tool: turning, from: 60mm, to: ___mm, length: ___mm}}
  Input edges from: NODE-OP1, NODE-OP2 (HARD DEPENDENCIES)
  Output edges to: [subsequent operations on this diameter]

[Create operation nodes for ALL features from Layer 0]

═══════════════════════════════════════════════════════════════
GRAPH LAYER 2: DEPENDENCY EDGE DEFINITION
═══════════════════════════════════════════════════════════════

Define all edges (dependencies) between operations:

HARD DEPENDENCIES (must complete before next can start):
- NODE-OP1 → NODE-OP3: [Reason: Need reference surface]
- NODE-OP2 → NODE-OP3: [Reason: Need length established]
- NODE-OP3 → NODE-OP4: [Reason: Must turn larger diameter before smaller]
[List ALL hard dependencies]

SOFT DEPENDENCIES (preferred order but not strictly required):
- NODE-OP___ → NODE-OP___: [Reason: ___]
[List any soft dependencies]

CONFLICT EDGES (operations that cannot overlap):
- NODE-OP___ ⟷ NODE-OP___: [Reason: Tool interference / Access blocked]
[List any conflicts]

═══════════════════════════════════════════════════════════════
GRAPH LAYER 3: PATH ANALYSIS
═══════════════════════════════════════════════════════════════

Identify all valid paths through the graph:

PATH 1: NODE-OP0 → NODE-OP1 → NODE-OP2 → NODE-OP3 → ...
  Length: ___ operations
  Critical path?: YES / NO
  Parallelization opportunities: [None / List nodes that could be parallel]

PATH 2: NODE-OP0 → [alternative sequence]
  Length: ___ operations
  Critical path?: YES / NO
  Parallelization opportunities: ___

[Analyze all valid paths]

CRITICAL PATH (longest dependency chain):
NODE-OP0 → NODE-OP___ → NODE-OP___ → ... → NODE-OP_FINAL
Total operations on critical path: ___
This represents the minimum number of sequential steps required.

═══════════════════════════════════════════════════════════════
GRAPH LAYER 4: GRAPH OPTIMIZATION
═══════════════════════════════════════════════════════════════

Optimize the graph structure:

MERGE OPPORTUNITIES:
- Can NODE-OP___ and NODE-OP___ be combined?: [Analysis]
- [Check all possible merges]

REORDER OPPORTUNITIES:  
- Can any operations be moved earlier/later to reduce critical path?: [Analysis]
- [Check all reordering options]

ADD MISSING NODES:
- Safety operations (chamfering): [Verify all needed]
- Quality checks: [If any]

FINAL GRAPH PROPERTIES:
- Total nodes: ___
- Total edges: ___
- Critical path length: ___
- Parallel operation opportunities: ___

═══════════════════════════════════════════════════════════════
GRAPH LAYER 5: WORKFLOW EXTRACTION
═══════════════════════════════════════════════════════════════

Extract the optimal linear workflow from the graph:

Perform topological sort on the dependency graph to get valid operation order:

OPERATION SEQUENCE (following all dependencies):
1. [NODE-OP___]: [Description]
   Dependencies satisfied: [List]
   
2. [NODE-OP___]: [Description]
   Dependencies satisfied: [List]

[Continue for all operations]

GRAPH VISUALIZATION:
[Represent your graph in text format showing nodes and edges]

Example:
NODE-OP0 (Initial)
  ↓
  ├→ NODE-OP1 (Face Left) ──┐
  │                         ↓
  └→ NODE-OP2 (Face Right)→ NODE-OP3 (Turn D1)
                                ↓
                            NODE-OP4 (Turn D2)
                                ↓
                              [...]

Output Format: {format_instructions}

Generate the final workflow now.
""",
    input_variables=['image', 'additional_text'],
    partial_variables={'format_instructions': output_parser.get_format_instructions()}
)

def generate_got_prompt(image_path: str, additional_text: str = "") -> str:
    """
    Convert the image to base64 and fill the prompt template with extra text.
    """
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64, additional_text=additional_text).to_string()
    return filled_prompt



def run_got(image_path: str, image_details: str = ""):
    """
    Run the TOT workflow with context of the image using the model and parse the output.
    """
    model = load_model(model_name='gemini-2.5-pro')

    prompt_str = generate_got_prompt(image_path=image_path, additional_text=image_details)

    raw_output = model.invoke(prompt_str)
    output_text = getattr(raw_output, 'content', str(raw_output))

    parsed_output = output_parser.parse(output_text)
    return parsed_output


if __name__ == "__main__":
    import json
    from src.workflow_1.image_understander.vlm_understander import run_vlm_for_image_understanding

    try:
        # image_path="data/curated_dataset/simple/simple_2.png"
        image_path="data/sample_images/sample_job.png"

        print("Running VLM to understand image.....")
        image_details = run_vlm_for_image_understanding(image_path=image_path)
        print(image_details)

        print("Generating workflow with image got .....")
        result = run_got(image_path=image_path, image_details=image_details)

        print(result)

    except Exception as e:
        print(f"Error!\nMessage: {e}")

    with open('temp/temp_got_hard.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)
