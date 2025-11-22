import io

import fitz  # PyMuPDF
from PIL import Image, ImageEnhance
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional


class PDFConversionConfig(BaseModel):
    """Configuration model for PDF to PNG conversion."""
    input_pdf: str = Field(default="AR2024_C.pdf", description="Input PDF file path")
    output_dir: str = Field(default="png_output", description="Output directory for PNG files")
    contrast_factor: float = Field(default=2.0, ge=0.0, description="Contrast enhancement factor")
    dpi: int = Field(default=300, gt=0, description="Resolution for rendering PDF pages")
    grayscale: bool = Field(default=True, description="Convert to grayscale")


def convert_pdf_to_png(config: PDFConversionConfig) -> None:
    """
    Convert PDF pages to individual PNG files in grayscale with increased contrast.
    
    Args:
        config: PDFConversionConfig instance with conversion settings
    """
    # Create output directory if it doesn't exist
    output_path = Path(config.output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Open the PDF file
    pdf_path = Path(config.input_pdf)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {config.input_pdf}")
    
    doc = fitz.open(config.input_pdf)
    
    print(f"Processing {len(doc)} pages from {config.input_pdf}")
    
    # Process each page
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to image (pixmap)
        mat = fitz.Matrix(config.dpi / 72, config.dpi / 72)  # Scale factor for DPI
        pix = page.get_pixmap(matrix=mat)
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to grayscale if requested
        if config.grayscale:
            img = img.convert("L")
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(config.contrast_factor)
        
        # Save the image
        output_filename = output_path / f"page_{page_num + 1:04d}.png"
        img.save(output_filename, "PNG")
        print(f"Saved: {output_filename}")
    
    num_pages = len(doc)
    doc.close()
    print(f"Conversion complete! {num_pages} pages processed.")


if __name__ == "__main__":
    # Create configuration with default values
    config = PDFConversionConfig(
        input_pdf="AR2024_C.pdf",
        output_dir="png_output",
        contrast_factor=2.0,
        dpi=300,
        grayscale=True
    )
    
    # Perform conversion
    try:
        convert_pdf_to_png(config)
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
