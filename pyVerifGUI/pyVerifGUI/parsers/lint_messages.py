###############################################################################
## File: parsers/lint_messages.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Functions to parse verilator linting messages"""

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


def clean_fields(fields: Sequence[str]) -> List[str]:
    """Strips out leading and lagging whitespace in parsed fields"""
    for i, field in enumerate(fields):
        fields[i] = field.strip()

    return fields

def parse_verilator_warning(matches: List[re.Match]) -> MessageListType:
    """Parses verilator output and returns a list of dictionaries containing warning information"""
    messages = []

    for match in matches:
        if match[0] != "Warning":
            continue

        messages.append({
            "file": match[3],
            "row": int(match[4]),
            "column": int(match[6]),
            "text": match[7],
            "text_hash": int(hashlib.md5(match[7].encode('utf-8')).hexdigest(), 16),
            "type": match[1][1:],
            "waiver": False,
            "comment": "N/A",
            "legitimate": False,
            "error": False,
        })

    return messages


def parse_verilator_error(matches: List[re.Match]) -> MessageListType:
    """Parses verilator output and returns a list of dictionaries containing errror info"""
    messages = []

    for match in matches:
        # Ignore errors w/o files
        if len(match[2]) == 0 or match[0] != "Error":
            continue

        # This is a parsing error, and shouldn't be treated the same way as other errors
        error_type = match[1][1:] if len(match[1]) != 0 else "Parse Error"
        messages.append({
            "file": match[3],
            "row": int(match[4]),
            "column": int(match[6]),
            "text": match[7],
            "text_hash": int(hashlib.md5(match[7].encode('utf-8')).hexdigest(), 16),
            "type": error_type,
            "waiver": False,
            "comment": "N/A",
            "legitimate": False,
            "error": True,
        })

    return messages


def parse_verilator_output(lint: str) -> MessageListType:
    """Parses verilator outputs for errors and warnings"""
    matches = verilator_parser.findall(lint)
    errors = parse_verilator_error(matches)
    warnings = parse_verilator_warning(matches)

    return errors + warnings
