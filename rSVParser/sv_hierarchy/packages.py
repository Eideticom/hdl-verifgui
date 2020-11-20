import pathlib
from typing import Tuple, List
from dataclasses import dataclass
from pathlib import Path

from py_sv_parser import SyntaxTree, unwrap_node


@dataclass
class SvPackage:
    name: str
    endname: str
    ports: List[Tuple]
    include: bool
    path: Path

def parse_tree(tree: SyntaxTree, path: Path):
    """Parses file tree for package information"""
    packages = []

    for node in tree:
        if node.type_name == "PackageDeclaration":
            name = unwrap_node(node, ["PackageIdentifier"])
            name = tree.get_str(name)

            packages.append(SvPackage(
                name, name, False, path
            ))

    return packages