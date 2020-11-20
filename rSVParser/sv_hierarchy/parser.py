from .includes import glob_files
from pathlib import Path
from yaml import dump
import argparse

from py_sv_parser import parse_sv

import sv_hierarchy.modules as modules
import sv_hierarchy.interfaces as interfaces
import sv_hierarchy.packages as packages
import sv_hierarchy.hierarchy as hierarchy

def main():
    """CLI access to functionality,

    mirrors usage of rSVParser
    """
    # CLI arguments
    args = argparse.ArgumentParser(description="Parsing utility to provide hierarchy and overview of SystemVerilog designs")
    args.add_argument("project_name", type=str, help="Name of the project, used in output directory")
    args.add_argument("--redo", "-r", help="Delete any old work.")
    args.add_argument("--top_module", action="store_true", help="Use the project name as the specified top module")
    args.add_argument("--include", "-I", type=str, nargs="*", help="Directories/files to include")
    args.add_argument("--pp-includes", type=str, nargs="*", help="Include dirs to pass to parser preprocessor")
    args.add_argument("--manual-pp-includes", action="store_true", help="Only pass manually specified include directoris to preprocessor")
    args.add_argument("--skip-sv", action="store_true", help="Ignore files with 'sv' extension")
    args.add_argument("--skip-v", action="store_true", help="Ignore files with 'v' extensions")
    args.add_argument("--extension", type=str, nargs="*", help="Add another file extension to parse as SV")
    args = args.parse_args()

    # Build list of extensions to search for
    extensions = []
    if not args.skip_sv:
        extensions.append("sv")
    if not args.skip_v:
        extensions.append("v")
    if args.extension is not None:
        extensions.extend(args.extension)

    # pathlib uses .ext vs PathBuf using ext
    # this maintains CLI compatability
    for extension in extensions:
        if not extension.startswith("."):
            extension = f".{extension}"

    # Create output dir
    base_path = Path(f"sv_{args.project_name}")
    base_path.mkdir(exist_ok=True)

    globs = glob_files(args.include, extensions, not args.manual_pp_includes)
    if args.pp_includes is not None:
        globs.includes.extend(args.pp_includes)
    sv_files, sv_modules, sv_interfaces, sv_packages = ({}, {}, {}, {})
    error = False
    includes = [str(inc) for inc in globs.includes]
    for file in globs.files:
        sv_files.update({file.name: {str(file): False}})

        tree = parse_sv(str(file), {}, includes, False, False)

        sv_modules.extend(modules.parse_tree(tree, file))
        sv_interfaces.extend(interfaces.parse_tree(tree, file))
        sv_packages.extend(packages.parse_tree(tree, file))

    # Build hierarchy
    if args.top_module:
        top_module = args.project_name
    else:
        top_module = None
    sv_hierarchy = hierarchy.build(sv_modules, top_module)

    # Set whether a given file has been included or not
    if args.top_module:
        for module in sv_modules.values():
            name = module.path.name
            sv_files[name][module.path] = True

    # Write to filesystem
    print(sv_modules)
    dump(open(str(base_path / "sv_modules.yaml"), "w"), sv_modules)
    dump(open(str(base_path / "sv_interfaces.yaml"), "w"), sv_interfaces)
    dump(open(str(base_path / "sv_packages.yaml"), "w"), sv_packages)
    dump(open(str(base_path / "sv_files.yaml"), "w"), sv_files)
    dump(open(str(base_path / "sv_hierarchy.yaml"), "w"), sv_hierarchy)


def backup_files(base_path: Path):
    """Saves copies of files from old parse runs"""
    for file in base_path.iterdir():
        if file.name.startswith("sv_") and file.suffix == ".yaml":
            file.rename(f"{file.name}.bak")


if __name__ == "__main__":
    main()
