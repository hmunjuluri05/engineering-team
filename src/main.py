#!/usr/bin/env python
"""Main entry point for the Engineering Team ADK application."""

import argparse
import sys
import warnings
from pathlib import Path

from .orchestrator import EngineeringTeam
from . import tools

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Engineering Team - Multi-agent software development automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Provide requirements from a file
  python -m src.main --requirements requirements.txt

  # Specify custom output directory
  python -m src.main --requirements my-project.txt --output my_output

  # Quiet mode (minimal progress information)
  python -m src.main --requirements requirements.txt --quiet

  # Using short flags
  python -m src.main -r requirements.txt -o build -q
"""
    )

    parser.add_argument(
        '--requirements', '-r',
        type=str,
        required=True,
        help='Path to a text file containing project requirements (required)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='output',
        help='Output directory for generated files (default: output)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode - show minimal progress information'
    )

    return parser.parse_args()


def get_requirements(requirements_path):
    """Load requirements from file path."""
    # Read requirements from file
    path = Path(requirements_path)
    if not path.exists():
        print(f"Error: Requirements file not found: {requirements_path}", file=sys.stderr)
        sys.exit(1)

    with open(path, 'r', encoding='utf-8') as f:
        requirements = f.read().strip()

    if not requirements:
        print(f"Error: Requirements file is empty: {requirements_path}", file=sys.stderr)
        sys.exit(1)

    return requirements


def run():
    """
    Run the engineering team workflow.
    """
    # Parse command-line arguments
    args = parse_args()

    # Get requirements
    requirements = get_requirements(args.requirements)
    output_dir = args.output

    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Set the output directory for tools
    tools.OUTPUT_DIR = output_dir

    print("=" * 80)
    print("Engineering Team ADK - Starting Workflow")
    print("=" * 80)
    print(f"Output Directory: {output_dir}")
    print(f"\nRequirements:\n{requirements}")
    print("=" * 80)

    # Create the engineering team
    team = EngineeringTeam(
        requirements=requirements,
        verbose=not args.quiet  # Verbose by default, unless --quiet is specified
    )

    # Run the workflow
    print("\nExecuting workflow...")
    result = team.run()

    print("\n" + "=" * 80)
    print("Workflow Complete!")
    print("=" * 80)
    print(f"\nCheck the '{output_dir}' directory for generated files:")
    print(f"\n  Root folder:")
    print(f"    - README.md - Installation and usage instructions")
    print(f"    - requirements.txt - Python dependencies")
    print(f"    - app.py - Gradio UI (if project needs a UI)")
    print(f"\n  docs/ folder:")
    print(f"    - DESIGN.md - Architecture and design specification")
    print(f"\n  src/ folder:")
    print(f"    - Backend Python code (e.g., main.py, models/, services/)")
    print(f"\n  tests/ folder:")
    print(f"    - Unit tests (if specified in the design)")
    print(f"\nThe file structure depends on project complexity as determined by the Engineering Lead.")
    print("=" * 80)

    return result


if __name__ == "__main__":
    run()
