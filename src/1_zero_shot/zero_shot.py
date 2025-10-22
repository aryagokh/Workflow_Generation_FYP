from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from src.utils import image_to_base64, load_model
from typing import List, Any
from PIL import Image
import warnings

warnings.filterwarnings(action='ignore')

class ZeroShotPrompt(BaseModel):
    steps: List[int] = Field(description="The step number, always int, start with 1 and increase by 1 everytime everystep")
    tool_name:List[str] = Field(description="List of all the tools used to maufacture the part, step wise")
    tool_speed:List[str] = Field(description="List of all the speeds (in rpm) of the tools used to maufacture the part, step wise")
    description:List[str] = Field(description="How the tool is being used for manufacturing the given part, step wise")
    counter: bool = Field(description="Recheck if all the steps are same in number, e.g. all above are 5 steps each, return True, else try to correct it until it is True")

output_parser = PydanticOutputParser(pydantic_object=ZeroShotPrompt)

template = PromptTemplate(
    template="""
You are an expert CNC workflow generation engineer.
Provided the image (attached separately), you have to generate a workflow to manufacture the part in the image given.

- Starting material: Solid cylindrical bar of cast iron
- Dimensions of raw stock: 100 mm length, 32 mm diameter
- Tools you have: Turning, Facing, Drilling, Chamfering, Step Turning (Use as per requirements)

You should specify what tool you are using and what speed is needed for the operation performed.

Image: {image}

Output Format: {format_instructions}

Start!
""",
input_variables=['image'],
partial_variables={'format_instructions': output_parser.get_format_instructions()}
)

def generate_zero_shot_prompt(image_path: str) -> str:
    img_b64 = image_to_base64(image_path)
    filled_prompt = template.format_prompt(image=img_b64).to_string()
    return filled_prompt

def run_zero_shot_workflow(image_path: str):
    model = load_model(
        model_name='gemini-2.5-pro'
    )
    prompt_str = generate_zero_shot_prompt(image_path)
    raw_output = model.invoke(prompt_str)

    if hasattr(raw_output, 'content'):
        output_text = raw_output.content
    else:
        output_text = str(raw_output)
    
    parsed_output = output_parser.parse(output_text)
    return parsed_output

if __name__ == "__main__":
    import json
    result = run_zero_shot_workflow("data/sample_images/tougher_sample.png")
    with open('temp/temp_zero_shot.json', 'w') as file:
        json.dump(result.model_dump(), file, indent=4)