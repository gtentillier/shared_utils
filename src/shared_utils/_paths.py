from pathlib import Path
from typing import Optional

path_project = (Path(__file__).resolve().parents[5])


def path_data(filename: Optional[str] = None) -> Path:
    """Get the path to the data directory, optionally appending a filename.
    Args:
        filename (Optional[str]): The name of the file to append to the data path.
    Returns:
        Path: The full path to the data directory or the specified file within it.
    """
    if filename is None:
        return path_project / 'data'
    else:
        return path_project / 'data' / filename


__all__ = ["path_project", "path_data"]
