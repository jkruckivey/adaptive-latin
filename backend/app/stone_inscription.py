"""
Stone Inscription Renderer
Generates Latin text styled as Roman stone inscriptions
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

# Font paths from canvas-design skill
FONTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "skills" / "canvas-design" / "canvas-fonts"

# Available serif fonts that work well for inscriptions
INSCRIPTION_FONTS = [
    "CrimsonPro-Bold.ttf",
    "IBMPlexSerif-Bold.ttf",
    "Lora-Bold.ttf",
    "LibreBaskerville-Regular.ttf",
    "YoungSerif-Regular.ttf"
]


def create_stone_inscription(
    text: str,
    output_path: str,
    width: int = 800,
    height: int = 300,
    font_size: int = 48,
    font_name: str = "CrimsonPro-Bold.ttf"
) -> str:
    """
    Create a stone inscription image with Latin text.

    Args:
        text: Latin text to inscribe
        output_path: Path to save the image
        width: Image width in pixels
        height: Image height in pixels
        font_size: Size of the inscription font
        font_name: Font file name from canvas-fonts

    Returns:
        Path to the generated image
    """
    # Create stone-colored background
    img = Image.new('RGB', (width, height), color='#8B7355')
    draw = ImageDraw.Draw(img)

    # Load font
    font_path = FONTS_DIR / font_name
    try:
        font = ImageFont.truetype(str(font_path), font_size)
    except Exception:
        # Fallback to default font
        font = ImageFont.load_default()

    # Add stone texture (noise)
    for _ in range(5000):
        import random
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        brightness = random.randint(-20, 20)
        original_color = img.getpixel((x, y))
        new_color = tuple(max(0, min(255, c + brightness)) for c in original_color)
        img.putpixel((x, y), new_color)

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw engraved text effect (shadow offset)
    shadow_color = '#5A4A3A'  # Darker stone
    draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)

    # Draw main text (lighter engraved appearance)
    text_color = '#D4C4B0'  # Lighter stone
    draw.text((x, y), text, font=font, fill=text_color)

    # Add subtle blur for weathered effect
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    # Save image
    img.save(output_path)
    return output_path


def create_tombstone_inscription(
    name: str,
    dates: str,
    epitaph: str,
    output_path: str,
    width: int = 600,
    height: int = 800
) -> str:
    """
    Create a Roman tombstone inscription.

    Args:
        name: Name in Latin (e.g., "MARCIA SECUNDA")
        dates: Dates/age (e.g., "ANN XXXV")
        epitaph: Epitaph text (e.g., "D M S")
        output_path: Path to save the image
        width: Image width
        height: Image height

    Returns:
        Path to the generated image
    """
    # Create darker stone background for tombstone
    img = Image.new('RGB', (width, height), color='#6B5D52')
    draw = ImageDraw.Draw(img)

    # Load fonts
    font_path_large = FONTS_DIR / "CrimsonPro-Bold.ttf"
    font_path_small = FONTS_DIR / "IBMPlexSerif-Bold.ttf"

    try:
        font_large = ImageFont.truetype(str(font_path_large), 56)
        font_medium = ImageFont.truetype(str(font_path_large), 40)
        font_small = ImageFont.truetype(str(font_path_small), 32)
    except Exception:
        font_large = font_medium = font_small = ImageFont.load_default()

    # Add stone texture
    import random
    for _ in range(8000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        brightness = random.randint(-25, 25)
        original_color = img.getpixel((x, y))
        new_color = tuple(max(0, min(255, c + brightness)) for c in original_color)
        img.putpixel((x, y), new_color)

    # Draw decorative border
    border_color = '#4A3D35'
    draw.rectangle([(20, 20), (width-20, height-20)], outline=border_color, width=3)

    # Text colors
    shadow_color = '#3A2D25'
    text_color = '#C4B4A0'

    # D M S (Dis Manibus Sacrum) at top
    y_pos = 80
    bbox = draw.textbbox((0, 0), epitaph, font=font_medium)
    text_width = bbox[2] - bbox[0]
    x_pos = (width - text_width) // 2
    draw.text((x_pos + 2, y_pos + 2), epitaph, font=font_medium, fill=shadow_color)
    draw.text((x_pos, y_pos), epitaph, font=font_medium, fill=text_color)

    # Name in center
    y_pos = 250
    bbox = draw.textbbox((0, 0), name, font=font_large)
    text_width = bbox[2] - bbox[0]
    x_pos = (width - text_width) // 2
    draw.text((x_pos + 2, y_pos + 2), name, font=font_large, fill=shadow_color)
    draw.text((x_pos, y_pos), name, font=font_large, fill=text_color)

    # Dates below
    y_pos = 400
    bbox = draw.textbbox((0, 0), dates, font=font_small)
    text_width = bbox[2] - bbox[0]
    x_pos = (width - text_width) // 2
    draw.text((x_pos + 2, y_pos + 2), dates, font=font_small, fill=shadow_color)
    draw.text((x_pos, y_pos), dates, font=font_small, fill=text_color)

    # Add weathering effect
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))

    # Save
    img.save(output_path)
    return output_path
