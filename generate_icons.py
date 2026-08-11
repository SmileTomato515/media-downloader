#!/usr/bin/env python3
"""
Generate icons for the Social Downloader app.
Style: Modern minimalist with blue color, download arrow and social media theme.
"""

from PIL import Image, ImageDraw
import os

# Create assets directory
os.makedirs('app/assets', exist_ok=True)

# Color palette
PRIMARY_BLUE = '#2563EB'  # Modern blue
DARK_BLUE = '#1E40AF'    # Darker shade
LIGHT_BLUE = '#DBEAFE'   # Light shade
WHITE = '#FFFFFF'
DARK_TEXT = '#1F2937'

def create_icon(size, filename):
    """Create main icon with download arrow and social circles"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    margin = size * 0.1
    circle_box = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_box, fill=PRIMARY_BLUE)
    
    # Inner design: Download arrow with social elements
    center_x, center_y = size / 2, size / 2
    
    # Draw three small circles representing social media platforms
    circle_radius = size * 0.08
    circle_y = center_y - size * 0.15
    
    # Left circle
    draw.ellipse(
        [center_x - size*0.15 - circle_radius, circle_y - circle_radius,
         center_x - size*0.15 + circle_radius, circle_y + circle_radius],
        fill=WHITE
    )
    # Center circle
    draw.ellipse(
        [center_x - circle_radius, circle_y - circle_radius,
         center_x + circle_radius, circle_y + circle_radius],
        fill=WHITE
    )
    # Right circle
    draw.ellipse(
        [center_x + size*0.15 - circle_radius, circle_y - circle_radius,
         center_x + size*0.15 + circle_radius, circle_y + circle_radius],
        fill=WHITE
    )
    
    # Draw download arrow
    arrow_width = size * 0.08
    arrow_height = size * 0.15
    
    # Arrow shaft (vertical line)
    shaft_x1 = center_x - arrow_width / 2
    shaft_x2 = center_x + arrow_width / 2
    shaft_y1 = center_y - arrow_height / 2
    shaft_y2 = center_y + arrow_height / 2
    
    draw.rectangle(
        [shaft_x1, shaft_y1, shaft_x2, shaft_y2],
        fill=WHITE
    )
    
    # Arrow head (triangle pointing down)
    arrow_head_size = size * 0.12
    arrow_head_y = center_y + arrow_height / 2
    
    triangle_points = [
        (center_x - arrow_head_size, arrow_head_y - arrow_head_size),
        (center_x + arrow_head_size, arrow_head_y - arrow_head_size),
        (center_x, arrow_head_y + arrow_head_size)
    ]
    draw.polygon(triangle_points, fill=WHITE)
    
    return img

def create_splash(width, height, filename):
    """Create splash screen with app name and logo"""
    img = Image.new('RGBA', (width, height), WHITE)
    draw = ImageDraw.Draw(img)
    
    # Background gradient effect (simplified with rectangle)
    # Top section with blue
    gradient_height = height // 3
    for i in range(gradient_height):
        alpha = int(255 * (1 - i / gradient_height))
        draw.rectangle(
            [(0, i), (width, i+1)],
            fill=(*hex_to_rgb(PRIMARY_BLUE), alpha)
        )
    
    # Main logo circle (larger version)
    center_x, center_y = width / 2, height / 3
    logo_size = min(width, height) // 4
    
    circle_box = [
        center_x - logo_size, center_y - logo_size,
        center_x + logo_size, center_y + logo_size
    ]
    draw.ellipse(circle_box, fill=PRIMARY_BLUE)
    
    # Social circles and arrow on splash
    circle_radius = logo_size * 0.15
    circle_y = center_y - logo_size * 0.2
    
    for offset in [-logo_size*0.3, 0, logo_size*0.3]:
        draw.ellipse(
            [center_x + offset - circle_radius, circle_y - circle_radius,
             center_x + offset + circle_radius, circle_y + circle_radius],
            fill=WHITE
        )
    
    # Download arrow
    arrow_shaft_height = logo_size * 0.25
    draw.rectangle(
        [center_x - logo_size*0.08, center_y, 
         center_x + logo_size*0.08, center_y + arrow_shaft_height],
        fill=WHITE
    )
    
    # Arrow head
    arrow_head_size = logo_size * 0.2
    triangle_points = [
        (center_x - arrow_head_size, center_y + arrow_shaft_height - arrow_head_size),
        (center_x + arrow_head_size, center_y + arrow_shaft_height - arrow_head_size),
        (center_x, center_y + arrow_shaft_height + arrow_head_size)
    ]
    draw.polygon(triangle_points, fill=WHITE)
    
    return img

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_favicon(size, filename):
    """Create small favicon with simplified design"""
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Small circle background
    margin = size * 0.1
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=PRIMARY_BLUE
    )
    
    # Simple download arrow (minimal design)
    center_x, center_y = size / 2, size / 2
    arrow_size = size * 0.25
    
    # Vertical line
    draw.rectangle(
        [center_x - size*0.05, center_y - arrow_size,
         center_x + size*0.05, center_y + arrow_size*0.5],
        fill=WHITE
    )
    
    # Triangle
    draw.polygon([
        (center_x - arrow_size*0.6, center_y),
        (center_x + arrow_size*0.6, center_y),
        (center_x, center_y + arrow_size*0.6)
    ], fill=WHITE)
    
    return img

# Generate all required icons
print("🎨 Generating Social Downloader icons...")

# Main app icon (1024x1024)
icon_1024 = create_icon(1024, 'app/assets/icon.png')
icon_1024.save('app/assets/icon.png', 'PNG')
print("✅ icon.png (1024x1024) created")

# Splash screen (1242x2436)
splash = create_splash(1242, 2436, 'app/assets/splash.png')
splash.save('app/assets/splash.png', 'PNG')
print("✅ splash.png (1242x2436) created")

# Adaptive icon for Android (1080x1080)
adaptive_icon = create_icon(1080, 'app/assets/adaptive-icon.png')
adaptive_icon.save('app/assets/adaptive-icon.png', 'PNG')
print("✅ adaptive-icon.png (1080x1080) created")

# Favicon for web (64x64)
favicon = create_favicon(64, 'app/assets/favicon.png')
favicon.save('app/assets/favicon.png', 'PNG')
print("✅ favicon.png (64x64) created")

print("\n✨ All icons generated successfully!")
print("📁 Files saved to: app/assets/")
