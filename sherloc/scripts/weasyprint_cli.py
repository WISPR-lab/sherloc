#!/usr/bin/env python3
"""Test CLI to investigate WeasyPrint rendering vs wkhtmltopdf.

Usage:
  python sherloc/scripts/weasyprint_cli.py reports/test_report.html reports/test_weasy.pdf

Options to try (edit in code):
  - DPI: default 96, try 72 (lower=more compact), try 120 (higher=bigger)
  - CSS adjustments: line-height, margins, padding
"""

import re
import sys
from pathlib import Path


def fix_image_urls(html_string: str, base_path: Path) -> str:
    """Convert image URLs to file paths so WeasyPrint can find them."""
    
    # Find all img src attributes and convert URLs to file:// paths
    def replace_src(match):
        src = match.group(1)
        
        # Skip data URIs
        if src.startswith('data:'):
            return match.group(0)
        
        # Strip leading slashes and convert to path relative to sherloc root
        path = src.lstrip('/')
        
        # Build absolute file path from sherloc root
        file_path = Path(__file__).parent.parent / path
        
        # If file exists, convert to file:// URL
        if file_path.exists():
            file_url = file_path.as_uri()
            return f'src="{file_url}"'
        else:
            # File doesn't exist, return original (might be a URL)
            return match.group(0)
    
    # Replace all src attributes
    html_string = re.sub(
        r'src=["\']([^"\']+)["\']',
        replace_src,
        html_string,
        flags=re.IGNORECASE
    )
    
    return html_string


def main() -> int:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.html> <output.pdf>", file=sys.stderr)
        return 1

    html_file = sys.argv[1]
    pdf_file = sys.argv[2]

    try:
        from weasyprint import HTML, CSS
    except Exception as exc:
        print("WeasyPrint is not installed. Run: pip install weasyprint", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 1

    html_path = Path(html_file)
    out_path = Path(pdf_file)

    if not html_path.exists():
        print(f"Input HTML not found: {html_path}", file=sys.stderr)
        return 1

    # Preset paths relative to script location
    script_dir = Path(__file__).parent.parent
    css_path = script_dir / "webstatic" / "style.css"

    html_string = html_path.read_text(encoding="utf-8")
    
    # Fix image URLs so WeasyPrint can find them
    html_string = fix_image_urls(html_string, html_path)
    
    # Set base_url to sherloc root for relative path resolution
    base_url = str(script_dir.resolve())

    css_objs = []
    if css_path.exists():
        css_objs.append(CSS(filename=str(css_path)))

    # Preset page settings matching pdfkit options
    page_css = """
@page {
  	/* A4(210mm 297mm) * 1.5  */
	size: 315mm 445.5mm;
  margin: 15mm 10mm 20mm 10mm;
  @bottom-center {
    content: "Created by Madison Tech Clinic using Sherloc • Page " counter(page) " of " counter(pages);
    font-family: Georgia, serif;
    font-size: 8pt;
  }
}

/* CSS to match wkhtmltopdf rendering more closely */
body {
  line-height: 1.15;
  font-size: 12px;
}

p {
  margin: 0.5em 0;
}

table {
  border-collapse: collapse;
  margin: 0.5em 0;
}

tr {
  page-break-inside: avoid;
}

h1, h2, h3, h4, h5, h6 {
  page-break-after: avoid;
  margin: 0.3em 0;
}
"""
    css_objs.append(CSS(string=page_css))

    # Try different DPI settings (default=96)
    # Experimenting: 72 DPI might make output more compact
    dpi = 96  # Change to 72 or 120 to test
    zoom = 1.2  # Scale down the output (0.75 = 75%, 0.68 = 68%, etc.)
    
    print(f"Rendering with DPI={dpi}, zoom={zoom}...")
    doc = HTML(string=html_string, base_url=base_url)
    doc.write_pdf(str(out_path), stylesheets=css_objs, dpi=dpi, zoom=zoom)
    print(f"✓ PDF written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
