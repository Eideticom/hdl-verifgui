###############################################################################
## File: gui/models/__init__.py
## Author: David Lenfesty
## Copyright (c) 2020. Eidetic Communications Inc.
## All rights reserved
## Licensed under the BSD 3-Clause license.
## This license message must appear in all versions of this code including
## modified versions.
##############################################################################
"""Various models and backend items for implementing the Models for MV controllers"""

from typing import Sequence, Mapping, Union

# I don't want to be more specific (i.e. use a TypedDict) until
# Messages are a little more bolted down.
# I would want to make a Message class before I get more specific than this.
MessageType = Mapping[str, Union[str, int, bool]]
MessageListType = Sequence[Mapping[str, Union[str, int, bool]]]

from .design import ModuleTreeItem, ModuleTreeItemModel
from .lint import LintMessageModel, DiffLintMessageModel, LintMessages, LintWaivers
