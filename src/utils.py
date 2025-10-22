from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.config import get_secret
from typing import Literal, Any
from PIL import Image
import warnings

warnings.filterwarnings(action='ignore')


def load_model(API_KEY:Literal['gemini', 'openai'] ='gemini', 
               model_name:str='gemini-2.5-flash-lite', 
               temperature:float=0.5)->Any:
    if API_KEY=='gemini':
        try:
            model = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                api_key=get_secret('GEMINI_API_KEY')
            )
            return model
        except Exception as e:
            print(f"Error: {e}")
    elif API_KEY=='openai':
        try:
            model = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                api_key=get_secret('OPENAI_API_KEY')
            )
            return model
        except Exception as e:
            print(f"Error: {e}")
            return 1
    else:
        print("No such model, please try passing correct ones! Options: GEMINI & OPENAI")


# def load_prompt(text_prompt:str, image_path: str)->Any:
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("human", [
#                 {"type": "text", "text": f"{text_prompt}"},
#                 {"type": "image_url", "image_url": {"url": Image.open(image_path)}},
#             ]),
#         ]
#     )

from PIL import Image
from io import BytesIO
import base64

def image_to_base64(image_path: str) -> str:
    image = Image.open(image_path)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return img_b64



if __name__ == '__main__':
    model = load_model()
    response = model.invoke("What is a CNC machine?")
    print(response.content)