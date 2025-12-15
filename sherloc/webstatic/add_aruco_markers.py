import fitz   # PyMuPDF, pip install PyMuPDF
from pathlib import Path

# Base project directory (this file is inside webstatic/)
BASE_DIR = Path(__file__).resolve().parent

# Input and output PDF
input_pdf = BASE_DIR / "test_report.pdf"
output_pdf = BASE_DIR / "test_report_marked.pdf"

# ArUco marker directory
ARUCO_DIR = BASE_DIR / "aruco"

# Marker paths
marker_paths = [
    ARUCO_DIR / "aruco_0.png",
    ARUCO_DIR / "aruco_1.png",
    ARUCO_DIR / "aruco_2.png",
    ARUCO_DIR / "aruco_3.png",
]

# Open original PDF
doc = fitz.open(str(input_pdf))

# Insert on every page
for page in doc:
    w, h = page.rect.width, page.rect.height
    marker_size = 90  # in points (~1.25 inches)
    margin = 36       # offset from page edges

    positions = [
        fitz.Rect(margin, margin,
                  margin + marker_size, margin + marker_size),                     # top-left
        fitz.Rect(w - margin - marker_size, margin,
                  w - margin, margin + marker_size),                               # top-right
        fitz.Rect(margin, h - margin - marker_size,
                  margin + marker_size, h - margin),                               # bottom-left
        fitz.Rect(w - margin - marker_size, h - margin - marker_size,
                  w - margin, h - margin),                                         # bottom-right
    ]

    for marker_path, pos in zip(marker_paths, positions):
        page.insert_image(pos, filename=str(marker_path))

# Save result
doc.save(str(output_pdf))
doc.close()

print("Done. Saved:", output_pdf)
