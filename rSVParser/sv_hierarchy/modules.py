from typing import Tuple, Dict, List
from dataclasses import dataclass
from pathlib import Path

from py_sv_parser import SyntaxTree, SyntaxNode, unwrap_node

from .ports import get_ports
from .helpers import get_str_or_default

# TODO params and ports should be split properly instead of into a big list
# TODO endname should be renamed
@dataclass
class SvModule:
    name: str
    parameters: List[Tuple] # 7 wide
    ports: List[Tuple] # 6 wide
    endname: str
    include: bool
    path: Path
    submodules: Dict[str, str]

def parse_tree(tree: SyntaxTree, path: Path) -> List[SvModule]:
    """Traverses tree for module declarations (and sub-instantiations)"""
    modules = []
    for node in tree:
        if node.type_name == "ModuleDeclaration":
            # Get module name
            name = unwrap_node(node, ["ModuleIdentifier"])
            name = tree.get_str(name)

            parameters = get_params(tree, node)

            ports = unwrap_node(node, ["ListOfPortDeclarations", "ListOfPorts"])
            if ports is None:
                print("    No Ports found!")
                ports = []
            else:
                ports = get_ports(tree, node)

            submodules = get_submodules(tree, node)

            modules.push(SvModule(
                name,
                parameters,
                ports,
                name,
                False,
                path,
                submodules
            ))

    return modules


def get_submodules(tree: SyntaxTree, module: SyntaxNode) -> Dict[str, str]:
    """Finds all submodules in module and returns their type and name"""
    submodules = {}

    for node in module:
        if node.type_name == "ModuleInstantiation":
            ident = unwrap_node(node, ["ModuleIdentifier"])
            ident = tree.get_str(ident)

            name = unwrap_node(node, ["InstanceIdentifier"])
            name = tree.get_str(ident)

            submodules.update({ident: name})

    return submodules

def get_params(tree: SyntaxTree, module: SyntaxNode) -> List[Tuple]:
    """Gets all of the parameters of a module"""
    params = []
    for node in module:
        if node.type_name == "ParameterDeclaration":
            name = unwrap_node(node, ["ParameterIdentifier"])
            name = tree.get_str(name)

            dimension = get_str_or_default(tree, node, "UnpackedDimension")
            value = get_str_or_default(tree, node, "ConstantParamExpression")

            params.append(("parameter", "", "", dimension, name, "", value))

    return params


