from typing import List, Tuple

from py_sv_parser import SyntaxTree, SyntaxNode, unwrap_node, unwrap_locate

from .helpers import get_str_or_default

def get_ports(
    tree: SyntaxTree,
    declaration: SyntaxNode
) -> List[Tuple]:
    """Pull all ANSI port declarations"""
    ports = []
    for node in declaration:
        if node.type_name == "AnsiPortDeclaration":
            direction = unwrap_node(node, ["PortDirection"])
            if direction is not None:
                direction = tree.get_str(direction).strip()
            else:
                direction = ""

            dimension = unwrap_node(node, ["PackedDimension"])
            if dimension is not None:
                dimension = tree.get_str(dimension).strip()
            else:
                dimension = ""

            name = unwrap_node(node, ["PortIdentifier"])
            name = unwrap_locate(name)
            name = tree.get_str(name)

            net_type = unwrap_node(node, ["NetType", "DataType"])
            if net_type is None:
                net_type = ""
            elif net_type.type_name == "NetType":
                net_type = tree.get_str(net_type).strip()
            elif net_type.type_name == "DataType":
                net_type = tree.get_str(net_type).split(" ")[0]

            ports.append((
                direction,
                net_type,
                "",
                dimension,
                name,
                ""
            ))

    return ports
