#!/usr/bin/env python3

import os

# Constants
STROKE_CUT = "rgb(255,0,0)"
STROKE_WIDTH = "0.2"

def generate_rectangle_svg(width_mm, height_mm, filename="rectangle.svg"):
    
    # Validation: 2 inches = 50.8 mm
    if width_mm > 50.8 or height_mm > 50.8:
        print("Error: Dimensions must be <= 50.8 mm (2 inches).")
        return False
    if width_mm <= 0 or height_mm <= 0:
        print("Error: Dimensions must be positive.")
        return False
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    filepath = os.path.join("output", filename)
    
    # SVG dimensions with margin
    svg_width = width_mm + 10
    svg_height = height_mm + 10
    
    # Rectangle position (centered with 5mm margin)
    x = 5
    y = 5
    
    # Write SVG file
    with open(filepath, 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n')
        f.write(f'<svg width="{svg_width}mm" height="{svg_height}mm" ')
        f.write(f'viewBox="0 0 {svg_width} {svg_height}" ')
        f.write('xmlns="http://www.w3.org/2000/svg">\n')
        f.write(f'  <g id="CUT" stroke="{STROKE_CUT}" stroke-width="{STROKE_WIDTH}" fill="none">\n')
        f.write(f'    <rect x="{x}" y="{y}" width="{width_mm}" height="{height_mm}" />\n')
        f.write('  </g>\n')
        f.write('</svg>\n')
    
    print(f"Successfully generated: {filepath}")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Task 1: Rectangle SVG Generator")
    print("Maximum dimensions: 2 inches (50.8 mm)")
    print("=" * 60)
    
    try:
        # Prompt user for dimensions
        width = float(input("Enter rectangle width in mm (max 50.8): "))
        height = float(input("Enter rectangle height in mm (max 50.8): "))
        
        # Generate the SVG
        generate_rectangle_svg(width, height, "task1_rectangle.svg")
        
    except ValueError:
        print("Error: Please enter valid numeric values.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
