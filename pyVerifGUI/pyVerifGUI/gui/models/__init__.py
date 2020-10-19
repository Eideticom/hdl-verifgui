###############################################################################
# @file pyVerifGUI/gui/models/__init__.py
# @package pyVerifGUI.gui.models
# @author David Lenfesty
# @copyright Copyright (c) 2020. Eidetic Communications Inc.
#            All rights reserved
# @license  Licensed under the BSD 3-Clause license.
#           This license message must appear in all versions of this code including
#           modified versions.
#
# @brief Models and backend items for implementing models in view widgets
##############################################################################

from typing import Sequence, Mapping, Union

# I don't want to be more specific (i.e. use a TypedDict) until
# Messages are a little more bolted down.
# I would want to make a Message class before I get more specific than this.
MessageType = Mapping[str, Union[str, int, bool]]
MessageListType = Sequence[Mapping[str, Union[str, int, bool]]]

from .design import ModuleTreeItem, ModuleTreeItemModel
from .lint import LintMessageModel, DiffLintMessageModel, LintMessages, LintWaivers
