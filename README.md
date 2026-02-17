# MECE 4606: Digital Manufacturing

Repository for Digital Manufacturing assignments and projects.

## 📂 File Structure

```text
.
├── README.md                 # Documentation
├── lamp_lattice/             # Project 2: Generative Lampshade
│   └── lamp.scad             # OpenSCAD script for lattice lamp
└── laser_cut/                # Project 1: Box Generator (V1 & V2)
    ├── v1/                   # Version 1 Codebase
    │   ├── box_generator.py  # Main CLI Application
    │   ├── output/           # Generated .svg files go here
    │   └── generate_scripts/ # Helper scripts for preset sizes
    └── v2/                   # Version 2 Codebase (In Development)
```

---

## 💡 Project 2: Lattice Lampshade

A procedural OpenSCAD script to generate a 3D printed lampshade with a lattice pattern.

### Features
- **Parametric Design**: Adjustable height, radii, and lattice density.
- **Generative Lattice**: Automatically creates a triangle lattice pattern on a conical surface.
- **Print Ready**: Designed to be stable and printable on Shapeways (SLS/SLA).

### Usage
1.  Open `lamp_lattice/lamp.scad` in OpenSCAD.
2.  Adjust parameters at the top of the file (e.g., `total_height`, `lattice_rows`).
3.  Press **F6** to render and export as STL.

---

## 📦 Project 1: Parametric Acrylic Box Generator

A Python tool to generate **fabrication-ready SVG files** for laser-cut acrylic boxes.

### Features
- **True Rectangular Dimensions**: Customize **Width**, **Depth**, and **Height**.
- **Finger Joints**: Dynamic tab generation for rigid assembly.
- **Engravings**: Sierpinski Triangle Fractal, Text Labels, Logos.

### Usage
Run the main script and follow the prompts:

```bash
python3 laser_cut/v1/box_generator.py
```

### Assembly
- **Materials**: 3mm Acrylic Sheet, Acrylic Cement.
- **Red Lines**: CUT (0.01mm stroke).
- **Blue Lines**: ENGRAVE (0.01mm stroke).

