import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
import io
import sys
import subprocess
import os
import re


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


def parse_markdown_by_pages(markdown_path: str):
    """Parse markdown file and split by page markers (## Page XXXX)."""
    if not Path(markdown_path).exists():
        return {}
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by page markers: ## Page XXXX
    # Pattern matches: ## Page followed by digits
    pattern = r'## Page (\d+)'
    pages = {}
    
    # Find all page markers
    matches = list(re.finditer(pattern, content))
    
    if not matches:
        # If no page markers, return entire content as page 1
        pages[0] = content
        return pages
    
    # Extract content for each page
    for i, match in enumerate(matches):
        page_num = int(match.group(1)) - 1  # Convert to 0-indexed
        start_pos = match.start()
        
        # Find end position (start of next page or end of file)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        # Extract page content (including the page marker)
        page_content = content[start_pos:end_pos].strip()
        pages[page_num] = page_content
    
    return pages


# Initialize session state
if "page_index" not in st.session_state:
    st.session_state.page_index = 0

# File paths
PDF_PATH = "AR2024_C.pdf"
MARKDOWN_PATH = "output.md"

# Load PDF
if not Path(PDF_PATH).exists():
    st.error(f"PDF file not found: {PDF_PATH}")
    st.stop()

pdf_doc, pdf_total_pages = load_pdf_pages(PDF_PATH)

# Load markdown pages
markdown_pages = parse_markdown_by_pages(MARKDOWN_PATH)
markdown_total_pages = max(markdown_pages.keys()) + 1 if markdown_pages else 0

if markdown_total_pages == 0:
    st.error(f"No markdown pages found in {MARKDOWN_PATH}")
    st.stop()

# Use minimum of both to ensure sync
total_pages = min(pdf_total_pages, markdown_total_pages)

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

# Two-column layout for PDF and Markdown
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("PDF View")
    try:
        pdf_img = render_pdf_page(pdf_doc, st.session_state.page_index)
        st.image(pdf_img, use_container_width=True)
    except Exception as e:
        st.error(f"Error rendering PDF page: {e}")

with col_right:
    st.subheader("Markdown View")
    try:
        if st.session_state.page_index in markdown_pages:
            markdown_content = markdown_pages[st.session_state.page_index]
            st.markdown(markdown_content)
        else:
            st.warning(f"Markdown content not available for page {st.session_state.page_index + 1}")
    except Exception as e:
        st.error(f"Error loading markdown: {e}")

# Close PDF document when done (though it will be reopened on rerun)
# We keep it open for the session to avoid repeated file I/O


def main():
    """Start Streamlit web service on port 8080."""
    # Get the path to the current script
    script_path = os.path.abspath(__file__)
    
    # Find streamlit executable
    streamlit_cmd = "streamlit"
    try:
        import shutil
        streamlit_cmd = shutil.which("streamlit") or "streamlit"
    except:
        pass
    
    # Start Streamlit server on port 8080
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        script_path,
        "--server.port=8080",
        "--server.address=127.0.0.1",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    
    print(f"Starting Streamlit web service on port 8080...")
    print(f"Access the application at: http://127.0.0.1:8080")
    print(f"Press Ctrl+C to stop the server")
    
    # Run the streamlit server
    subprocess.run(cmd)


if __name__ == "__main__":
    # Only start server if run directly (not when Streamlit imports this file)
    # Check if streamlit is in the command line args (indicating we're already running)
    if "streamlit" not in " ".join(sys.argv).lower():
        main()

