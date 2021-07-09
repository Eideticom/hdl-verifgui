from typing import List
import sys

from _pytest.config.argparsing import Parser
from _pytest.reports import TestReport
from _pytest.config import Config, PytestPluginManager
from pytest import Item, Session

# 
output_enabled = False

# Functions roughly sorted in order of hooks being called

def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager):
    """Adds CLI flag required for plugin to run, so that installation of
    hdl-verifgui doesn't mess with other uses of pytest.
    """
    parser.addoption("--hdl-verifgui", action="store_true",
                     help="Enable hdl-verifgui output, only use with '-p no:terminalreporter'")


def pytest_configure(config: Config):
    """Checks if CLI flag has been set"""
    global output_enabled
    output_enabled = config.getoption("--hdl-verifgui", default=False)


def pytest_collection_modifyitems(session: Session, config: Config, items: List[Item]):
    """Print information about collected items in a parseable way.

    This is done to collect test IDs and information related to them.
    """
    if not output_enabled:
        return

    for item in items:
        markers = [mark.name for mark in item.iter_markers()]
        coverage = "coverage" in markers
        regression = "regression" in markers
        print(f"COLLECT,{item._nodeid},{coverage},{regression}")

    # Flush is necessary because otherwise output gets cached until the end of the run.
    sys.stdout.flush()


def pytest_runtest_logreport(report: TestReport):
    """Final reports after tests run"""
    if not output_enabled:
        return

    print(f"REPORT,{report.nodeid},{report.when},{report.outcome},{report.duration}")
    # Flush is necessary because otherwise output gets cached until the end of the run.
    sys.stdout.flush()

