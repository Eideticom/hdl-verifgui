from typing import List, Union
from dataclasses import asdict
from pathlib import Path
from yaml import dump
import argparse

from py_sv_parser import parse_sv

from .includes import glob_files
import sv_hierarchy.modules as modules
import sv_hierarchy.interfaces as interfaces
import sv_hierarchy.packages as packages
import sv_hierarchy.hierarchy as hierarchy


# TODO surface print statements as a library somehow

def main():
    """CLI access to functionality,

    mirrors usage of rSVParser
    """
    # CLI arguments
    args = argparse.ArgumentParser(description="Parsing utility to provide hierarchy and overview of SystemVerilog designs")
    args.add_argument("project_name", type=str, help="Name of the project, used in output directory")
    args.add_argument("--redo", "-r", help="Delete any old work.")
    args.add_argument("--top_module", action="store_true", help="Use the project name as the specified top module")
    args.add_argument("--include", "-I", type=str, action="append", help="Directories/files to include")
    args.add_argument("--pp-includes", type=str, action="append", help="Include dirs to pass to parser preprocessor")
    args.add_argument("--manual-pp-includes", action="store_true", help="Only pass manually specified include directoris to preprocessor")
    args.add_argument("--skip-sv", action="store_true", help="Ignore files with 'sv' extension")
    args.add_argument("--skip-v", action="store_true", help="Ignore files with 'v' extensions")
    args.add_argument("--extension", type=str, action="extend", help="Add another file extension to parse as SV")
    args = args.parse_args()


    # Build list of extensions to search for
    extensions = []
    if not args.skip_sv:
        extensions.append("sv")
    if not args.skip_v:
        extensions.append("v")
    if args.extension is not None:
        extensions.extend(args.extension)

    # Decide if we want a top module
    if args.top_module:
        top_module = args.project_name
    else:
        top_module = None

    # pathlib uses .ext vs PathBuf using ext
    # this maintains CLI compatability
    for i in range(len(extensions)):
        if not extensions[i].startswith("."):
            extensions[i] = f".{extensions[i]}"

    # Create output dir
    base_path = Path(f"sv_{args.project_name}")
    base_path.mkdir(exist_ok=True)
    backup_files(base_path)

    globs = glob_files(args.include, extensions, not args.manual_pp_includes)
    if args.pp_includes is not None:
        globs.includes.extend(args.pp_includes)

    out = parse_files(globs.files, globs.includes, top_module)

    # Write to filesystem
    #print("Writing outputs...")
    dump(out["sv_modules"], open(str(base_path / "sv_modules.yaml"), "w"))
    dump(out["sv_interfaces"], open(str(base_path / "sv_interfaces.yaml"), "w"))
    dump(out["sv_packages"], open(str(base_path / "sv_packages.yaml"), "w"))
    dump(out["sv_files"], open(str(base_path / "sv_files.yaml"), "w"))
    dump(out["sv_hierarchy"], open(str(base_path / "sv_hierarchy.yaml"), "w"))


def parse_files(files: List[Path], includes: List[Path], top_module: Union[None, str]) -> dict:
    sv_files, sv_modules, sv_interfaces, sv_packages = ({}, {}, {}, {})
    includes = [str(inc) for inc in includes]
    for file in files:
        sv_files.update({file.name: {str(file): False}})

        #print(f"Parsing file {file}...")
        tree = parse_sv(str(file), {}, includes, False, False)

        for mod in modules.parse_tree(tree, file):
            #print(f"- Found module {mod.name}")
            sv_modules.update({mod.name: mod})
        for interface in interfaces.parse_tree(tree, file):
            #print(f"- Found module {interface.name}")
            sv_interfaces.update({interface.name: interface})
        for package in packages.parse_tree(tree, file):
            #print(f"- Found module {package.name}")
            sv_packages.update({package.name: package})

    # Build hierarchy
    sv_hierarchy = hierarchy.build(sv_modules, top_module)

    # Set whether a given file has been included or not
    if top_module:
        for module in sv_modules.values():
            name = module.path.name
            sv_files[name][str(module.path)] = True

    # Convert custom types to dicts
    for mod in sv_modules:
        sv_modules[mod] = asdict(sv_modules[mod])
        sv_modules[mod]["parameters"] = [list(param) for param in sv_modules[mod]["parameters"]]
        sv_modules[mod]["ports"] = [list(port) for port in sv_modules[mod]["ports"]]
        sv_modules[mod]["path"] = str(sv_modules[mod]["path"])
    for interface in sv_interfaces:
        sv_interfaces[interface] = asdict(sv_interfaces[interface])
        sv_interfaces[interface]["ports"] = [list(port) for port in sv_interfaces[interface]["ports"]]
        sv_interfaces[interface]["path"] = str(sv_interfaces[interface]["path"])
    for pkg in sv_packages:
        sv_packages[pkg] = asdict(sv_packages[pkg])
        sv_packages[pkg]["ports"] = [list(port) for port in sv_packages[pkg]["ports"]]
        sv_packages[pkg]["path"] = str(sv_packages[pkg]["path"])
    for hier in sv_hierarchy:
        sv_hierarchy[hier] = asdict(sv_hierarchy[hier])

    return {
        "sv_modules": sv_modules,
        "sv_interfaces": sv_interfaces,
        "sv_packages": sv_packages,
        "sv_files": sv_files,
        "sv_hierarchy": sv_hierarchy,
    }


def backup_files(base_path: Path):
    """Saves copies of files from old parse runs"""
    for file in base_path.iterdir():
        if file.name.startswith("sv_") and file.suffix == ".yaml":
            file.rename(base_path / f"{file.name}.bak")


if __name__ == "__main__":
    main()
