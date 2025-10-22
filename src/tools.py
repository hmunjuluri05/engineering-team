"""Tools for file output and utilities."""

from pathlib import Path
from typing import Optional

# Module-level variable for output directory (can be configured from main.py)
OUTPUT_DIR = "output"


def save_to_file(content: str, filename: str, output_dir: Optional[str] = None) -> str:
    """
    Save content to a file in the specified output directory.

    Args:
        content: The content to write to the file
        filename: The name of the file to create
        output_dir: The directory to save the file in (default: uses OUTPUT_DIR)

    Returns:
        A confirmation message with the file path
    """
    # Use the module-level OUTPUT_DIR if not specified
    if output_dir is None:
        output_dir = OUTPUT_DIR

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Construct full file path
    file_path = Path(output_dir) / filename

    # Create parent directories if they don't exist (e.g., for "src/main.py", create "src" folder)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return f"Successfully saved content to {file_path}"
