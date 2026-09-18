"""
Create a small synthetic demo dataset for spoilage detection.
Generates simple colored images to simulate 'GOOD' and 'SPOILED' classes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

GOOD_DIR = Path('food_data/datasets/good_food_images')
SPOILED_DIR = Path('food_data/datasets/spoilage_images')

GOOD_DIR.mkdir(parents=True, exist_ok=True)
SPOILED_DIR.mkdir(parents=True, exist_ok=True)

def make_image(path: Path, color: tuple, text: str):
    img = Image.new('RGB', (224,224), color=color)
    draw = ImageDraw.Draw(img)
    try:
        f = ImageFont.load_default()
        draw.text((10,100), text, fill=(255,255,255), font=f)
    except Exception:
        draw.text((10,100), text, fill=(255,255,255))
    img.save(path)

def generate(n=20):
    for i in range(n):
        # Good images: bright, fresh colors
        color = (random.randint(120,255), random.randint(140,255), random.randint(80,240))
        make_image(GOOD_DIR / f'good_{i}.jpg', color, 'GOOD')

    for i in range(n):
        # Spoiled images: darker, brown/green tones
        color = (random.randint(30,140), random.randint(20,120), random.randint(10,100))
        make_image(SPOILED_DIR / f'spoiled_{i}.jpg', color, 'SPOILED')

if __name__ == '__main__':
    generate(30)
    print('Demo dataset created with 30 GOOD and 30 SPOILED images in', GOOD_DIR, SPOILED_DIR)
