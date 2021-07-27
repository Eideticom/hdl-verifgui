###############################################################################
# @file pyVerifGUI/parsers/lint_messages.py
# @package pyVerifGUI.parsers.lint_messages
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Verilator message parsers (warnings and errors)
##############################################################################

import hashlib
from typing import Sequence, List
import re

from pyVerifGUI.gui.models import MessageListType

# Modified version of RE from verilator manual
# Group descriptions
# 1: Error/warning
# 2: optional lint type (e.g. TIMESCALEMOD)
# 3: optional file:line:column
# 4: file
# 5: line
# 6: optional column
# 7: column
# 8: Rest of the error
verilator_parser = re.compile(r"%(Error|Warning)(-[A-Z0-9_]+)?: (([^\s:]+):(\d+):((\d+):)? )?(.*)")


def parse_verilator_output(lint: str) -> (MessageListType, List[str]):
    """Parses verilator outputs for errors and warnings"""
    matches = verilator_parser.findall(lint)

    messages: MessageListType = []
    errors: List[str] = []
    for match in matches:
        if match[0] == "Warning":
            # Linting/parsing warnings
            messages.append({
                "file": match[3],
                "lineno": int(match[4]),
                "column": int(match[6]),
                "text": match[7],
                "text_hash": int(hashlib.md5(match[7].encode('utf-8')).hexdigest(), 16),
                "type": match[1][1:],
                "waiver": False,
                "comment": "N/A",
                "legitimate": False,
                "error": False,
            })
        elif match[0] == "Error" and len(match[2]) != 0:
            # Linting/parsing errors
            error_type = match[1][1:] if len(match[1]) != 0 else "Parse Error"
            messages.append({
                "file": match[3],
                "lineno": int(match[4]),
                "column": int(match[6]),
                "text": match[7],
                "text_hash": int(hashlib.md5(match[7].encode('utf-8')).hexdigest(), 16),
                "type": error_type,
                "waiver": False,
                "comment": "N/A",
                "legitimate": False,
                "error": True,
            })
        elif match[0] == "Error" and len(match[2]) == 0:
            # General verilator errors
            errors.append(match[-1])

    return messages, errors
