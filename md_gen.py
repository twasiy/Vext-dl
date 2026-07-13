from pathlib import Path


def generate_markdown_from_py(root_dir, output_file, ignore_list=None):
    if ignore_list is None:
        ignore_list = set()

    root_path = Path(root_dir).resolve()

    with open(output_file, "w", encoding="utf-8") as md_file:
        md_file.write(f"# Project Source Code: {root_path.name}\n\n")

        # rglob("*") finds all files recursively
        for file_path in root_path.rglob("*.py"):

            # Check if filename or any part of the path is in the ignore list
            # (e.g., skips 'venv', '__pycache__', or specific filenames)
            if (
                any(ignored in file_path.parts for ignored in ignore_list)
                or file_path.name in ignore_list
            ):
                continue

            try:
                # Calculate path relative to the root for the header
                relative_path = file_path.relative_to(root_path)

                md_file.write(f"## File: `{relative_path}`\n\n")
                md_file.write("```python\n")

                with open(file_path, "r", encoding="utf-8") as f:
                    md_file.write(f.read())

                md_file.write("\n```\n\n---\n\n")
                print(f"Processed: {relative_path}")

            except Exception as e:
                print(f"Could not read {file_path}: {e}")


if __name__ == "__main__":
    # --- CONFIGURATION ---
    # The directory you want to scan
    target_directory = "."

    # The name of the resulting markdown file
    output_markdown = "project_codebase.md"

    # Add filenames or directory names you want to skip
    skip_these = {
        "venv",
        "__pycache__",
        ".venv",
        "setup.py",
        "__init__.py",
        "templates",
        "tests",
        "migrations",
        "md_gen.py",
        ".env",
        ".env.example",
        ".gitignore",
        "alembic.ini",
        "LICENSE",
        "pytest.ini",
        "README.md",
        "requirements.txt",
    }

    generate_markdown_from_py(target_directory, output_markdown, skip_these)
    print(f"\nDone! File saved to: {output_markdown}")
