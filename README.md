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

### Files
- **`lamp_lattice/lamp_v1.scad`**:
    - **Design**: Conical body with a regular triangle lattice pattern.
    - **Base**: Features a 5-point star cutout.
    - **Color**: Rendered in Green.
- **`lamp_lattice/lamp_v2.scad`**:
    - **Design**: Twisted, undulating body with a randomized "jittered" lattice (guaranteed >5mm spacing).
    - **Features**: Integrated circular top collar for light fitting.
    - **Base**: Plain circular base.

### Features
- **Parametric Design**: Adjustable height, radii, and lattice density.
- **Print Ready**: Designed to be stable and printable on Shapeways (SLS/SLA).
- **Socket Fit**: Designed for a light fixture with 18mm height, 37.4mm base dia, 36.2mm top dia.

### Usage
1.  Open `lamp_lattice/lamp_v1.scad` or `lamp_lattice/lamp_v2.scad` in OpenSCAD.
2.  Adjust parameters at the top of the file if needed.
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

