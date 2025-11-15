from pydantic_ai import Agent, RunContext, ModelSettings
from langfuse import get_client
from dotenv import load_dotenv
from models import MarkSixResult
load_dotenv()
 
langfuse = get_client()
 
# Verify connection
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
    Agent.instrument_all()
else:
    print("Authentication failed. Please check your credentials and host.")

agent = Agent(
    'openrouter:google/gemini-2.5-flash-lite',
    instrument=True,
    system_prompt=langfuse.get_prompt('initialprompt2').compile()
)

## ## For debug test
# p = langfuse.get_prompt('initialprompt', label='production')
# print(p.compile())


# Mark Six Vision Agent (delegate for image analysis)
mark_six_vision_agent = Agent(
    'openrouter:google/gemini-2.5-flash-lite',
    instrument=True,
    system_prompt=langfuse.get_prompt('markdsixprompt2').compile(),
    output_type=MarkSixResult
)


## ## For debug test
# p2 = langfuse.get_prompt('markfixprompt', label='production')
# print(p2.compile())


@agent.tool
def calculator(ctx: RunContext, number1: float, number2: float, operation: str) -> float:
    """Perform simple arithmetic operations.
    
    Args:
        ctx: Run context
        number1: First number
        number2: Second number
        operation: Operation to perform (add, subtract, multiply, divide)
    
    Returns:
        Result of the calculation
    """
    if operation == 'add':
        return number1 + number2
    elif operation == 'subtract':
        return number1 - number2
    elif operation == 'multiply':
        return number1 * number2
    elif operation == 'divide':
        if number2 == 0:
            raise ValueError("Cannot divide by zero")
        return number1 / number2
    else:
        raise ValueError(f"Unsupported operation: {operation}")


@agent.tool
async def extract_mark_six_from_image(ctx: RunContext, image_path: str) -> str:
    """Extract Mark Six lottery results from an image using vision agent delegation.
    
    Args:
        ctx: Run context
        image_path: Path to the local image file containing Mark Six results
    
    Returns:
        JSON string representing the extracted MarkSixResult
    """
    from pathlib import Path
    from pydantic_ai import BinaryContent
    
    # Validate file exists and read image data
    path = Path(image_path)
    if not path.exists():
        raise ValueError(f"Image file not found: {image_path}")
    
    image_data = path.read_bytes()
    
    # Delegate to vision agent with image using BinaryContent
    result = await mark_six_vision_agent.run(
        [
            "Extract the Mark Six lottery results from this image.",
            BinaryContent(data=image_data, media_type='image/png'),
        ],
        usage=ctx.usage,  # Track usage in parent context
    )
    
    # Return the validated structured result as JSON
    # result.output is already a MarkSixResult instance due to output_type
    return result.output.model_dump_json()


# Demo 1: Calculator Tool
print("=" * 50)
print("Demo 1: Calculator Tool")
print("=" * 50)

result1 = agent.run_sync("What is 125 multiplied by 48?")
print(f"Question: What is 125 multiplied by 48?")
print(f"Answer: {result1.output}\n")

result2 = agent.run_sync("Calculate 1000 divided by 25")
print(f"Question: Calculate 1000 divided by 25")
print(f"Answer: {result2.output}\n")

# Demo 2: Mark Six Result Extractor
print("=" * 50)
print("Demo 2: Mark Six Result Extractor")#
print("=" * 50)
result3 = agent.run_sync(
    "Please extract the lottery results from the image at: ./sample_data/mark6_result.png"
)
print(f"Question: Extract lottery results from ./sample_data/mark6_result.png")
print(f"Answer: {result3.output}\n")