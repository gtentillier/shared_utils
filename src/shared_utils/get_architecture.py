from pathlib import Path
from typing import List, Union

keep_project_root: bool = False  # Set to True if you want to keep the project root in the architecture output

folder_to_exclude: List[str] = [
    ".venv",
    ".git",
    ".github",
    ".vscode",
    "notebooks",
    "default_project_name.egg-info",
    "__pycache__",
]

file_end_to_exclude: List[str] = [
    "__init__.py",
    ".md",
    ".txt",
    "architecture",
    "LICENCE",
    ".ipynb",
    ".DS_Store",
]

files_to_keep: List[str] = [
    "copilot-instructions.md",
    "empty.chatmode.md",
    "requirements.txt",
    ".gitignore",
]

folder_to_exclude_inner: List[str] = []


def ignore_file(file_name: str) -> bool:
    """Check if a file should be ignored based on its name.

    Args:
        file_name (str): Name of the file.

    Returns:
        bool: True if the file should be ignored.
    """
    if file_name in files_to_keep:
        return False
    return file_name.endswith(tuple(file_end_to_exclude))


def generate_architecture(root_dir: Union[str, Path], output_file: Union[str, Path]) -> None:
    """Generate a textual representation of the project structure and save it to a file.

    Args:
        root_dir (Union[str, Path]): The root directory of the project.
        output_file (Union[str, Path]): The path to the output text file.
    """
    root_path: Path = Path(root_dir)
    output_path: Path = Path(output_file)
    tree_lines: List[str] = []

    def recurse_dir(current_dir: Path, prefix: str = "") -> None:
        try:
            entries = sorted([p for p in current_dir.iterdir()], key=lambda p: p.name)
        except OSError as e:
            tree_lines.append(f"{prefix}Error accessing {current_dir}: {e}")
            return

        directories: List[Path] = []
        files: List[Path] = []
        for entry in entries:
            if entry.is_dir():
                if entry.name in folder_to_exclude:
                    continue
                directories.append(entry)
            else:
                if ignore_file(entry.name):
                    continue
                files.append(entry)

        children: List[Path] = directories + files
        count: int = len(children)

        for index, child in enumerate(children):
            connector = "└──" if index == count - 1 else "├──"
            tree_lines.append(f"{prefix}{connector} {child.name}")
            if child.is_dir():
                if child.name in folder_to_exclude_inner:
                    continue
                extension = "    " if index == count - 1 else "│   "
                recurse_dir(child, prefix + extension)

    if keep_project_root:
        tree_lines.append(f"{root_path.name}")
    recurse_dir(root_path)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(tree_lines), encoding="utf-8")
    except Exception as e:
        print(f"Error writing to file {output_path}: {e}")


if __name__ == "__main__":
    project_root = Path.cwd()
    output_path = project_root / "architecture"
    generate_architecture(project_root, output_path)
    print(f"\n📐 Project architecture saved to {output_path}")
