import torch
from diffusers import I2VGenXLPipeline
from diffusers.utils import export_to_gif, load_image
from PIL import Image
from transformers.image_utils import load_image
from transformers import AutoProcessor, AutoModelForVision2Seq
import torch

import gc
torch.cuda.empty_cache()
gc.collect()

pipe = I2VGenXLPipeline.from_pretrained("ali-vilab/i2vgen-xl", torch_dtype=torch.float16, variant="fp16")
pipe.enable_model_cpu_offload()


def image2video(img, prompt, id):
    # image_url = "https://huggingface.co/datasets/diffusers/docs-images/resolve/main/i2vgen_xl_images/img_0009.png"
    image = img.copy()

    #prompt = prompt #"The man is holding a helmet in his left hand and raising his right arm."
    negative_prompt = "Distorted, discontinuous, Ugly, blurry, low resolution, motionless, static, disfigured, disconnected limbs, Ugly faces, incomplete arms"
    generator = torch.manual_seed(8888)
    frames = pipe(
        prompt=prompt,
        image=image,
        num_inference_steps=50,
        negative_prompt=negative_prompt,
        guidance_scale=9.0,
        generator=generator
    ).frames[0]
    export_to_gif(frames, str(id)+"_generate.gif", fps=10)
    return str(id)+"_generate.gif"



DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM-Instruct")

model = AutoModelForVision2Seq.from_pretrained(
    "HuggingFaceTB/SmolVLM-Instruct",
    torch_dtype=torch.bfloat16
).to("cuda")

def image2discript(img, prompt="Can you describe the image?"):


    # Load images
    image1 = img.copy()

    # Create input messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": prompt} #Please write a good short script that is well suited for creating an animation of this picture?
            ]
        },
    ]

    # Prepare inputs
    prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
    inputs = processor(text=prompt, images=[image1], return_tensors="pt")
    inputs = inputs.to(DEVICE)
    # Generate outputs
    generated_ids = model.generate(**inputs, max_new_tokens=77)
    generated_texts = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True,
    )

    prompt = generated_texts[0].split('Assistant:')[1]
    return prompt