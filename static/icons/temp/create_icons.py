#!/usr/bin/env python3
from PIL import Image, ImageDraw
import os

# Ensure directory exists
os.makedirs('static/icons', exist_ok=True)

# Create blue square with rounded corners for each size
sizes = [72, 96, 128, 144, 152, 192, 384, 512]
blue_color = (74, 111, 255)  # #4A6FFF

for size in sizes:
    # Create a new image with blue background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a blue rounded rectangle
    # For simplicity, we'll just draw a blue circle as a placeholder
    draw.ellipse((0, 0, size, size), fill=blue_color)
    
    # Save the image
    output_path = f'static/icons/icon-{size}x{size}.png'
    img.save(output_path)
    print(f'Generated {output_path}')

# Generate favicon.ico
favicon = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
draw = ImageDraw.Draw(favicon)
draw.ellipse((0, 0, 32, 32), fill=blue_color)
favicon.save('static/icons/favicon.ico')
print('Generated static/icons/favicon.ico')