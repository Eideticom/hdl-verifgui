###############################################################################
# @file pyVerifGUI/tasks/runners.py
# @package pyVerifGUI.tasks.runners
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Helper functions for running tasks
##############################################################################

import os
import sys
import shutil
import subprocess as sp
import random
import tempfile
import hashlib
from pathlib import Path
from oyaml import safe_load, dump
from typing import Union, List

from pyVerifGUI.gui.config import Config, ConfigError
from .worker import Worker

from pyVerifGUI.parsers import parse_verilator_output


def create_rtlfiles_list(top_module, sv_rtl_fileslist_filename, sv_cfg_data):
    if not top_module in sv_cfg_data['sv_hierarchy']:
        print(
            f"<ERROR>'{top_module}' not found in hiearchy tree (sv_hierarchy.yaml)"
        )
        sys.exit(1)

    htree = sv_cfg_data['sv_hierarchy'][top_module]['tree']

    def get_modules(blk_dict: dict):
        modules = list(blk_dict.keys())
        for branch in blk_dict.values():
            modules.extend(get_modules(branch))

        return modules

    modules = get_modules(htree)
    files_lst = []
    for pkg_data in sv_cfg_data['sv_packages'].values():
        if pkg_data['path'] not in files_lst:
            files_lst.append(pkg_data['path'])

    for if_data in sv_cfg_data['sv_interfaces'].values():
        if if_data['path'] not in files_lst:
            files_lst.append(if_data['path'])

    for mdl_name in modules:
        try:
            mdl = sv_cfg_data['sv_modules'][mdl_name]
            if mdl['path'] not in files_lst:
                files_lst.append(mdl['path'])
        except KeyError:
            # This happens when external modules are used, such as FPGA intrinsics
            pass

    posix_pathlst = [Path(path).as_posix() for path in files_lst]
    with Path(sv_rtl_fileslist_filename).open('w') as fptr:
        fptr.write("\n".join(posix_pathlst))


def get_extra_args(args: Union[str, None]) -> List:
    """Pares out extra args and add to a string"""
    if args is not None:
        args = args.strip()
        if args:
            return args.strip().split(" ")

    return []


class SVParseWorker(Worker):
    def fn(self, stdout, config: Config):
        """Run the SystemVerilog parser and save its output to the build
        directory
        """
        # Check if rSVParser exists first
        try:
            thing = sp.run(["rSVParser", "-h"], capture_output=True)
            self.cmd_list = ["rSVParser"]
        except FileNotFoundError:
            return (
                -1, "",
                "rSVParser not found! Please ensure it is installed and in your PATH."
            )

        self.cmd_list = ["rSVParser", config.top_module, "--top_module"]
        for path in config.rtl_dir_paths:
            self.cmd_list.extend(["--include", str(path)])

        parse_args = config.config.get("parse_args", None)
        self.cmd_list.extend(get_extra_args(parse_args))
        self.display_cmd()

        try:
            self.popen = sp.Popen(self.cmd_list,
                                  stdout=sp.PIPE,
                                  stderr=sp.PIPE,
                                  cwd=config.working_dir_path)
        except Exception as exc:
            return (-1, "", str(exc))
        returncode, stdout = self.emit_stdout("parser")
        _, stderr = self.popen.communicate()

        if returncode != 0:
            # Necessary, because when the parser fails, the required files often do not exist
            return (returncode, stdout, stderr.decode())

        # Copy output to build directory
        working_parse_path = config.build_path / f"sv_{config.top_module}"

        # Generate list of files for linter to use
        modules = safe_load(open(str(working_parse_path / "sv_modules.yaml")))
        hierarchy = safe_load(
            open(str(working_parse_path / "sv_hierarchy.yaml")))
        packages = safe_load(open(str(working_parse_path /
                                      "sv_packages.yaml")))
        interfaces = safe_load(
            open(str(working_parse_path / "sv_interfaces.yaml")))
        sv_cfg = {
            "sv_modules": modules,
            "sv_hierarchy": hierarchy,
            "sv_packages": packages,
            "sv_interfaces": interfaces,
        }
        create_rtlfiles_list(config.top_module,
                             str(config.build_path / "rtlfiles.lst"), sv_cfg)

        return (returncode, stdout, stderr.decode())


class LinterWorker(Worker):
    def fn(self, stdout, config: Config):
        """Run verilator as a linter and save the parsed output into the build
        directory.
        """
        del stdout

        if os.name == 'nt':
            verilator_exe = "verilator.exe"
        else:
            verilator_exe = "verilator"

        self.cmd_list = [verilator_exe, "--lint-only", "-Wall", "--top-module",
                         config.top_module, "-f", f"{config.build_path.resolve()}/rtlfiles.lst"]

        opts = config.config.get("verilator_args", None)
        self.cmd_list.extend(get_extra_args(opts))
        self.display_cmd()

        # can only be run after parsing has finished
        try:
            self.popen = sp.Popen(self.cmd_list,
                                  stdout=sp.PIPE,
                                  stderr=sp.PIPE,
                                  cwd=config.working_dir_path)
        except Exception as exc:
            return (-42, "", str(exc))

        stdout, stderr = self.popen.communicate()
        stderr = stderr.decode()
        returncode = self.popen.wait()
        message_text = stderr

        # Parse verilator output to build list of messages
        messages, errors = parse_verilator_output(message_text)
        if messages is None:
            return (-42, "", message_text)

        # Write messages to YAML storage file
        messages_path = config.build_path / "linter_messages.yaml"
        dump(messages, open(messages_path, "w"))

        errors_path = config.build_path / "linter_errors.yaml"
        if errors:
            dump(errors, open(errors_path, "w"))
        else:
            if errors_path.exists():
                os.remove(str(errors_path))

        return (returncode, stdout.decode(), stderr)
