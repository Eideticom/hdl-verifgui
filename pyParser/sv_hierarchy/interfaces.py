from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path

from py_sv_parser import SyntaxTree, unwrap_node

from .helpers import get_str_or_default
from .ports import get_ports

@dataclass
class SvInterface:
    name: str
    endname: str
    ports: List[Tuple]
    include: bool
    path: Path


def parse_tree(tree: SyntaxTree, path: Path) -> List[SvInterface]:
    """Traverse tree for any interfaces"""
    interfaces = []
    for node in tree:
        if node.type_name == "InterfaceDeclaration":
            name = get_str_or_default(tree, node, "InterfaceIdentifier")

            ports = get_ports(tree, node)

            interfaces.append(SvInterface(
                name,
                name,
                ports,
                False,
                path
            ))

    return interfaces