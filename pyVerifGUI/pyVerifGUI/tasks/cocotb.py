###############################################################################
# @file pyVerifGUI/tasks/cocotb_collect.py
# @package pyVerifGUI.tasks.cocotb
# @author David Lenfesty
# @copyright Copyright (c) 2021. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Common types for all CocoTB-related tasks
##############################################################################
from dataclasses import dataclass
from typing import List, Set, Union, Tuple


@dataclass
class CollectedTest:
    name: str
    parameters: List[Union[List[str], Set[str]]]
    coverage: bool
    regression: bool


@dataclass
class Test:
    module: str
    name: str
    parameters: Tuple[str]

    def __str__(self) -> str:
        return f"{self.module}::{self.name}[{'-'.join(self.parameters)}]"


def test_from_nodeid(nodeid: str) -> Test:
    pass

