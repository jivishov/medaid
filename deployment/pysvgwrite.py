import svgwrite

def create_color_palette_svg(filename="medaid_palette_and_logo.svg"):
    dwg = svgwrite.Drawing(filename, size=("800px", "600px"))
    
    # Color palettes
    palettes = [
        {"name": "Medical Blue + Tech Green", "colors": ["#0077BE", "#00CC66", "#FFFFFF"]},
        {"name": "Navy Blue + Coral Orange", "colors": ["#003366", "#FF6633", "#F0F0F0"]},
        {"name": "Teal Blue + Amber", "colors": ["#008080", "#FFA500", "#FFFFFF"]},
        {"name": "Royal Blue + Electric Green", "colors": ["#4169E1", "#39FF14", "#F8F8F8"]},
        {"name": "Cerulean + Tangerine", "colors": ["#007BA7", "#FFA07A", "#FFFFFF"]}
    ]
    
    # Draw color palettes
    for i, palette in enumerate(palettes):
        y_offset = i * 50 + 50
        dwg.add(dwg.text(palette["name"], insert=(10, y_offset - 5), fill="#333333", font_size="14px"))
        for j, color in enumerate(palette["colors"]):
            dwg.add(dwg.rect(insert=(10 + j * 60, y_offset), size=(50, 30), fill=color, stroke="#000000", stroke_width=1))
            dwg.add(dwg.text(color, insert=(10 + j * 60, y_offset + 45), fill="#333333", font_size="10px"))

    # Draw logo concept
    logo_group = dwg.g(transform="translate(400, 300) scale(2)")
    
    # "med" part
    logo_group.add(dwg.text("med", insert=(0, 0), fill="#0077BE", font_size="40px", font_family="Arial, sans-serif"))
    
    # Custom "a" with pill-shaped counter
    a_path = dwg.path(d="M70 0 Q85 0 85 -20 Q85 -40 70 -40 H55 V0 H70 M55 -20 H70 Q75 -20 75 -30 Q75 -40 70 -40 H55 V-20", fill="#00CC66")
    logo_group.add(a_path)
    
    # "i" dot forming part of the cross
    logo_group.add(dwg.circle(center=(95, -35), r=3, fill="#00CC66"))
    
    # Modified "d" with extended ascender forming cross
    d_path = dwg.path(d="M105 0 V-50 H120 Q135 -50 135 -35 Q135 -20 120 -20 H105 M105 0 H120 Q135 0 135 -15 Q135 -30 120 -30 H105", fill="#00CC66")
    logo_group.add(d_path)
    
    # Cross in negative space
    logo_group.add(dwg.line(start=(95, -32), end=(95, -20), stroke="#00CC66", stroke_width=2))
    logo_group.add(dwg.line(start=(90, -26), end=(100, -26), stroke="#00CC66", stroke_width=2))
    
    dwg.add(logo_group)
    
    # Save the SVG file
    dwg.save()

# Generate the SVG
create_color_palette_svg()
print("SVG file 'medaid_palette_and_logo.svg' has been created.")