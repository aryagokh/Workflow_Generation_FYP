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


class InstructionsCOTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    all_reasoning_process: str = Field("All the reasoning process from start to end, that lead to final decision about the plan")


output_parser = PydanticOutputParser(pydantic_object=InstructionsCOTPrompt)


template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer.
Provided the image (attached separately) and the additional instructions below, you have to generate a workflow to manufacture the part in the image given.

- Starting material: Solid cylindrical bar of cast iron
- Dimensions of raw stock: 120 mm length, 60 mm diameter
- Tools you have: Turning, Facing, Drilling, Chamfering, Step Turning, Taper Turning (Use as per requirements)

Details about the image (what the image actually says, you can validate it if needed): {additional_text}

Image: {image}

Important: 
Start with making all diameters uniform first. 
For eg. if there are 3 diameters like 40, 20, and 30 and workpiece is 45, the whole part should be made 40 first and then machined for the respective lengths, then done 30 and then 20 along with their respective lengths needed. Takke this as a genetric example and it is excluded from what is actually in the part shown.
Facing is to be done on both sides for making sides uniform.
Turning is used to reduce diameters.
Taper turning is used when diameters are not perpendicular but there is a V taper that connects them, or diameters are reducing from point a to point b in a certain way.
Chamfering is done on sharp edges to avoid injuries to humans.
Drilling is done as required if shown in image.
Think step by step and reason through each operation before giving the final workflow.

Output Format: {format_instructions}

Start!
""",
    input_variables=['image', 'additional_text'],
    partial_variables={'format_instructions': output_parser.get_format_instructions()}
)



def generate_instructions_cot_prompt(image_path: str, additional_text: str = "") -> str:
    """
    Convert the image to base64 and fill the prompt template with extra text.
    """
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64, additional_text=additional_text).to_string()
    return filled_prompt



def run_instructions_cot(image_path: str, image_details: str = ""):
    """
    Run the Instructions COT workflow with context of the image using the model and parse the output.
    """
    model = load_model(model_name='gemini-2.5-pro')

    prompt_str = generate_instructions_cot_prompt(image_path=image_path, additional_text=image_details)

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
        result = run_instructions_cot(image_path=image_path, image_details=image_details)

        print(result)

    except Exception as e:
        print(f"Error!\nMessage: {e}")

    with open('temp/temp_instructions_cot.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)
