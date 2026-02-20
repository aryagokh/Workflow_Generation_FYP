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


class COTPrompt(BaseModel):
    steps: List[Step] = Field(..., description="List of all manufacturing steps")
    all_reasoning_process: str = Field("All the reasoning process from start to end, that lead to final decision about the plan")


output_parser = PydanticOutputParser(pydantic_object=COTPrompt)


template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer.
Provided the image (attached separately) and the additional instructions below, you have to generate a workflow to manufacture the part in the image given.

- Starting material: Solid cylindrical bar of cast iron
- Dimensions of raw stock: 120 mm length, 60 mm diameter
- Tools you have: Turning, Facing, Drilling, Chamfering, Step Turning (Use as per requirements)

Details about the image (what the image actually says, you can validate it if needed): {additional_text}

Image: {image}

Important: Think step by step and reason through each operation before giving the final workflow.

Output Format: {format_instructions}

Start!
""",
    input_variables=['image', 'additional_text'],
    partial_variables={'format_instructions': output_parser.get_format_instructions()}
)



def generate_cot_prompt_with_context(image_path: str, additional_text: str = "") -> str:
    """
    Convert the image to base64 and fill the prompt template with extra text.
    """
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64, additional_text=additional_text).to_string()
    return filled_prompt



def run_cot_workflow_with_context(image_path: str, image_details: str = ""):
    """
    Run the cot workflow with context of the image using the model and parse the output.
    """
    model = load_model(model_name='gemini-2.5-pro')

    prompt_str = generate_cot_prompt_with_context(image_path=image_path, additional_text=image_details)

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

        print("Generating workflow with image aware cot .....")
        result = run_cot_workflow_with_context(image_path=image_path, image_details=image_details)

        print(result)

    except Exception as e:
        print(f"Error!\nMessage: {e}")

    with open('temp/temp_cot.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)
