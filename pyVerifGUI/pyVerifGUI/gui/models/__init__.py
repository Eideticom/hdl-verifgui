"""Various models and backend items for implementing the Models for MV controllers"""

__author__ = "David Lenfesty"
__copyright__ = "Copyright (c) 2020 Eidetic Communications"

from typing import Sequence, Mapping, Union

# I don't want to be more specific (i.e. use a TypedDict) until
# Messages are a little more bolted down.
# I would want to make a Message class before I get more specific than this.
MessageType = Mapping[str, Union[str, int, bool]]
MessageListType = Sequence[Mapping[str, Union[str, int, bool]]]

from .design import ModuleTreeItem, ModuleTreeItemModel
from .lint import LintMessageModel, DiffLintMessageModel, LintMessages, LintWaivers
