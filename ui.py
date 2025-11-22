import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
import io
import sys
import subprocess
import os


def load_pdf_pages(pdf_path: str):
    """Load PDF and return total page count."""
    doc = fitz.open(pdf_path)
    return doc, len(doc)


def render_pdf_page(doc, page_num: int, dpi: int = 150):
    """Render a specific PDF page as PIL Image."""
    page = doc[page_num]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_data))
    return img


def load_png_files(png_dir: str):
    """Load and sort PNG files from directory."""
    png_path = Path(png_dir)
    if not png_path.exists():
        return []
    
    png_files = sorted(png_path.glob("page_*.png"), key=lambda x: int(x.stem.split("_")[1]))
    return [str(f) for f in png_files]


# Initialize session state
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

# File paths
PDF_PATH = "AR2024_C.pdf"
PNG_DIR = "png_output"

# Load PDF
if not Path(PDF_PATH).exists():
    st.error(f"PDF file not found: {PDF_PATH}")
    st.stop()

pdf_doc, pdf_total_pages = load_pdf_pages(PDF_PATH)

# Load PNG files
png_files = load_png_files(PNG_DIR)
png_total_pages = len(png_files)

if png_total_pages == 0:
    st.error(f"No PNG files found in {PNG_DIR}")
    st.stop()

# Use minimum of both to ensure sync
total_pages = min(pdf_total_pages, png_total_pages)

# Ensure page_index is within valid range
if st.session_state.page_index >= total_pages:
    st.session_state.page_index = total_pages - 1
if st.session_state.page_index < 0:
    st.session_state.page_index = 0

# Navigation buttons
col1_btn, col2_btn, col3_btn = st.columns([1, 2, 1])

with col1_btn:
    if st.button("⬅️ Previous", disabled=(st.session_state.page_index == 0)):
        st.session_state.page_index -= 1
        st.rerun()

with col2_btn:
    st.write(f"**Page {st.session_state.page_index + 1} of {total_pages}**")

with col3_btn:
    if st.button("Next ➡️", disabled=(st.session_state.page_index >= total_pages - 1)):
        st.session_state.page_index += 1
        st.rerun()

st.divider()

# Two-column layout for PDF and PNG
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("PDF View")
    try:
        pdf_img = render_pdf_page(pdf_doc, st.session_state.page_index)
        st.image(pdf_img, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering PDF page: {e}")

with col_right:
    st.subheader("PNG View")
    try:
        if st.session_state.page_index < len(png_files):
            png_path = png_files[st.session_state.page_index]
            png_img = Image.open(png_path)
            st.image(png_img, use_container_width=True)
        else:
            st.warning("PNG file not available for this page")
    except Exception as e:
        st.error(f"Error loading PNG: {e}")

# Close PDF document when done (though it will be reopened on rerun)
# We keep it open for the session to avoid repeated file I/O


def main():
    """Start Streamlit web service on port 80."""
    # Get the path to the current script
    script_path = os.path.abspath(__file__)
    
    # Find streamlit executable
    streamlit_cmd = "streamlit"
    try:
        import shutil
        streamlit_cmd = shutil.which("streamlit") or "streamlit"
    except:
        pass
    
    # Start Streamlit server on port 80
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        script_path,
        "--server.port=80",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    print(f"Starting Streamlit web service on port 80...")
    print(f"Access the application at: http://localhost:80")
    print(f"Press Ctrl+C to stop the server")
    
    # Run the streamlit server
    subprocess.run(cmd)


if __name__ == "__main__":
    # Only start server if run directly (not when Streamlit imports this file)
    # Check if streamlit is in the command line args (indicating we're already running)
    if "streamlit" not in " ".join(sys.argv).lower():
        main()

