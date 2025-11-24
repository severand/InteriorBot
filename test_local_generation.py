from diffusers import StableDiffusionPipeline
import torch

print("Loading model... (это займёт время при первом запуске)")

# Загружаем модель Stable Diffusion
pipeline = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32
)

print("✓ Model loaded!")

# Генерируем изображение
print("Generating image...")
image = pipeline("A modern minimalist living room with natural light").images[0]

# Сохраняем
image.save("generated_image.png")
print("✓ Image saved as generated_image.png")
