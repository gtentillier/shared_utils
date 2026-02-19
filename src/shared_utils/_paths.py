import os
from pathlib import Path

# Use environment variable if it exists, otherwise fallback to relative path (fragile but preserved for local dev)
path_project = Path(os.getenv("SHARED_UTILS_PROJECT_ROOT", Path(__file__).resolve().parents[5]))

path_data = path_project / 'data'
