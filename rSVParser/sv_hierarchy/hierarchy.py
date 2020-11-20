from dataclasses import dataclass
from typing import Dict, Union
from pathlib import Path

from .modules import SvModule


@dataclass
class SvHierarchy:
    include: bool
    tree: dict

def build(modules: Dict[str, SvModule], top_module: Union[None, str]) -> Dict[str, SvHierarchy]:
    """Builds a hierarchy out of a list of modules"""

    # Build out list of top-level modules
    top = list(modules.keys())
    for module in modules.values():
        for submod in module.submodules.keys():
            # Remove any modules found in other modules.
            # This leaves only top level modules
            if top_module is not None:
                top = filter(lambda mod: mod == top_module or mod != submod, top)
            else:
                top = filter(lambda mod: mod != submod)

    print("Ignoring modules not found in files")
    defined_modules = list(modules.keys())
    top = filter(lambda mod: mod in defined_modules, top)

    yaml_out = {}
    for module in top:
        hier = {module: build_tree(module, modules)}

        if module == top_module:
            include = True
        else:
            include = False

        yaml_out.update({module: SvHierarchy(
            include,
            hier
        )})

    return yaml_out

def build_tree(top: str, modules: Dict[str, SvModule]) -> dict:
    """Builds out the tree to describe a module's hierarchy"""
    module = modules.get(top)
    if module:
        map = {}
        for submod in module.submodules.keys():
            map.update({submod: build_tree(submod, modules)})

        return map

    else:
        return {}
