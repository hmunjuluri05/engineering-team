"""Tools for file output and utilities."""

from pathlib import Path

# Module-level variable for output directory (MUST be set from main.py before use)
OUTPUT_DIR = None


def save_to_file(content: str, filename: str) -> str:
    """
    Save content to a file in the specified output directory.

    Args:
        content: The content to write to the file
        filename: The name of the file to create

    Returns:
        A confirmation message with the file path

    Raises:
        RuntimeError: If OUTPUT_DIR has not been configured
    """
    # Use the module-level OUTPUT_DIR configured in main.py
    if OUTPUT_DIR is None:
        raise RuntimeError(
            "OUTPUT_DIR has not been configured. "
            "This should be set from main.py using tools.OUTPUT_DIR = output_dir"
        )
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
