import asyncio
from pathlib import Path
from PIL import Image
from pydantic_ai import Agent, BinaryContent

from langfuse import get_client
from dotenv import load_dotenv
load_dotenv()
 
langfuse = get_client()

# Verify langfuse connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
    Agent.instrument_all()
else:
    print("Authentication failed. Please check your credentials and host.")





async def process_png_files():
    """
    Read PNG files from png_output folder in order and extract text using PydanticAI vision agent.
    Uses Pillow to open images and PydanticAI for text extraction.
    Appends extracted text to output.md in markdown format.
    """
    png_dir = Path("png_output")
    output_file = Path("output.md")
    
    if not png_dir.exists():
        raise FileNotFoundError(f"Directory not found: {png_dir}")
    
    # Create vision agent for text extraction
    vision_agent = Agent(
        'openrouter:google/gemini-2.5-flash-lite',
        system_prompt="Extract all text from the provided image. Return the extracted text in markdown format, preserving the structure and formatting as much as possible."
    )
    
    # Clear or create output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# OCR Extracted Text\n\n")
    
    # Process PNG files in order starting from page_0001.png
    page_num = 1
    processed_count = 0
    
    while True:
        png_file = png_dir / f"page_{page_num:04d}.png"
        
        if not png_file.exists():
            break
        
        print(f"Processing: {png_file}")
        
        try:
            # Open image using Pillow for validation
            with Image.open(png_file) as img:
                # Validate image can be opened and processed
                img.load()
            
            # Read image bytes directly from file
            image_data = png_file.read_bytes()
            
            # Create BinaryContent for PydanticAI
            binary_content = BinaryContent(data=image_data, media_type='image/png')
            
            # Extract text using PydanticAI vision agent
            result = await vision_agent.run(
                [
                    "Extract all text from this image and format it in markdown. Preserve the structure, tables, and formatting as much as possible.",
                    binary_content,
                ]
            )
            
            # Get extracted text from result
            extracted_text = result.output if isinstance(result.output, str) else str(result.output)
            
            # Append to output.md with markdown formatting
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"## Page {page_num:04d}\n\n")
                f.write(f"{extracted_text}\n\n")
                f.write("---\n\n")
            
            processed_count += 1
            page_num += 1
            
        except Exception as e:
            print(f"Error processing {png_file}: {e}")
            # Append error note to output file
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"## Page {page_num:04d}\n\n")
                f.write(f"*Error processing this page: {str(e)}*\n\n")
                f.write("---\n\n")
            page_num += 1
            continue
    
    print(f"\nProcessing complete! {processed_count} pages processed.")
    print(f"Output saved to: {output_file}")


def main():
    """Main entry point for the script."""
    try:
        asyncio.run(process_png_files())
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
