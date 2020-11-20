from dataclasses import dataclass
from pathlib import Path
from typing import List
from glob import glob

@dataclass
class GlobResults:
    files: List[Path]
    includes: List[Path]

def glob_files(patterns: List[str], extensions: List[str], add_includes: bool) -> GlobResults:
    """Do all of our file globbing"""
    files = []
    includes = []

    for inc in patterns:
        path = Path(inc)
        if path.exists():
            if path.is_file() and path.suffix in extensions:
                if path not in files:
                    files.append(path)
            elif path.is_dir():
                add_directory(path, extensions, add_includes, files, includes)
        else:
            paths = glob(inc, recursive=True)
            for path in paths:
                path = Path(path)
                if path.is_file() and path.suffix in extensions:
                    if path not in files:
                        files.append(path)
                    if add_includes and path.parent not in includes:
                        includes.append(path.parent)
                elif path.is_dir():
                    add_directory(path, extensions, add_includes, files, includes)

    return GlobResults(files, includes)


def add_directory(path: Path, extensions: List[str], add_includes: bool,
                  files: List[Path], includes: List[Path]):
    files_included = False
    for file in path.iterdir():
        if file.is_file() and file.suffix in extensions:
            files_included = True
            if file not in files:
                files.append(file)

    if files_included and add_includes and path not in includes:
        includes.append(path)
