from typing import List, Tuple

from py_sv_parser import SyntaxTree, SyntaxNode, unwrap_node

from .helpers import get_str_or_default

def get_ports(
    tree: SyntaxTree,
    declaration: SyntaxNode
) -> List[Tuple]:
    """Pull all ANSI port declarations"""
    ports = []
    for node in declaration:
        if node.type_name == "AnsiPortDeclaration":
            direction = get_str_or_default(tree, node, "PortDirection")
            dimension = get_str_or_default(tree, node, "PackedDimension")
            name = unwrap_node(node, ["PortIdentifier"])
            name = tree.get_str(name)

            net_type = unwrap_node(node, ["NetType", "DataType"])
            if net_type is None:
                net_type = ""
            elif net_type.type_name == "NetType":
                net_type = tree.get_str(net_type).strip()
            elif net_type.type_name == "DataType":
                net_type = next(tree.get_str(net_type).split(" "))

            ports.append((
                direction,
                net_type,
                "",
                dimension,
                name,
                ""
            ))

    return ports
