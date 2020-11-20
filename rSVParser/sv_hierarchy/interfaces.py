from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path

from py_sv_parser import SyntaxTree, unwrap_node


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
            name = unwrap_node(node, "InterfaceIdentifier")
            name = tree.get_str(name)

            ports = unwrap_node(node, ["ListOfPortDeclarations", "ListOfPorts"])
            if ports is None:
                print("    No Ports found!")
                ports = []


            interfaces.push(SvInterface(
                name,
                name,
                ports,
                False,
                path
            ))

    return interfaces