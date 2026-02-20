import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
import json

def load_understander_model():
    print("Loading Qwen 2.5 VL 3B (Unsloth 4-bit)...")
    torch.cuda.empty_cache()
    
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        "unsloth/Qwen2.5-VL-3B-Instruct-unsloth-bnb-4bit", 
        dtype="auto", 
        device_map="auto"
    )

    # # We recommend enabling flash_attention_2 for better acceleration and memory saving, especially in multi-image and video scenarios.
    # model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    #     "Qwen/Qwen2.5-VL-3B-Instruct",
    #     torch_dtype=torch.bfloat16,
    #     attn_implementation="flash_attention_2",
    #     device_map="auto",
    # )
    
    processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")
    print("Model Loaded Successfully!")
    return model, processor


def extract_features(image_path, model, processor):
    """
    Takes an image path and returns the extracted geometric features text.
    """
    
    system_prompt = """
    What are the dimensions given in the image for engineering part, from left to right? Please specify what part it is (example diameter, length, pair, chamfer etc) and keep it in pair (like diameter and length of one cylinder will be together.)
    """
    
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": image_path,
                },
                {"type": "text", "text": system_prompt},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda")

    generated_ids = model.generate(**inputs, max_new_tokens=512)
    generated_ids_trimmed = [
        out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )
    
    return output_text[0]


def run_vlm_for_image_understanding(image_path: str):
    model, processor = load_understander_model()
    print(f"Analyzing image from: {image_path}...")
    result = extract_features(image_path, model, processor)

    return result




if __name__ == "__main__":
    image_path = "data/curated_dataset/simple/simple_2.png"
    
    try:
        result = run_vlm_for_image_understanding(image_path=image_path)
        
        print("\n--- Extracted Data ---")
        print(result)
        print("----------------------")
        
    except Exception as e:
        print(f"Error: {e}")