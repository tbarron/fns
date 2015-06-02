import os
import pdb
import pytest
import time


# -----------------------------------------------------------------------------
def pytest_addoption(parser):
    """
    Add the --logpath option to the command line
    """
    parser.addoption("--logpath", action="store", default="",
                     help="where to write a test log")
    parser.addoption("--dbg", action="append", default=[],
                     help="start debugger on test named or ALL")

# -----------------------------------------------------------------------------
def pytest_report_header(config):
    """
    Put marker in the log file to show where the test run started
    """
    write_testlog(config, "-" * 60)
    return("")
    # return("Float'n'sink version %s" % __version__)


# -----------------------------------------------------------------------------
def pytest_runtest_setup(item):
    """
    For each test, just before it runs...
    """
    if any([item.name in item.config.getoption("--dbg"),
            'all' in item.config.getoption("--dbg")]):
        pytest.debug_func = pdb.set_trace
    else:
        pytest.debug_func = lambda: None


# -----------------------------------------------------------------------------
def pytest_unconfigure(config):
    """
    At the end of the run, log a summary
    """
    write_testlog(config,
                  "passed: %d; FAILED: %d" % (write_testlog._passcount,
                                              write_testlog._failcount))


# -----------------------------------------------------------------------------
@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    """
    Write a line to the log file for this test
    """
    rep = __multicall__.execute()
    if rep.when != 'call':
        return rep

    if rep.outcome == 'failed':
        status = ">>>>FAIL"
        write_testlog._failcount += 1
    else:
        status = "--pass"
        write_testlog._passcount += 1

    parent = item.parent
    msg = "%-8s %s:%s.%s" % (status,
                             os.path.basename(parent.fspath.strpath),
                             parent.name,
                             item.name)
    write_testlog(item.config, msg)
    return rep


# -----------------------------------------------------------------------------
def write_testlog(config, loggable):
    """
    Here's where we actually write to the log file is one was specified
    """
    logpath = config.getoption("logpath")
    if logpath == "":
        return
    f = open(logpath, 'a')
    msg = "%s %s\n" % (time.strftime("%Y.%m%d %H:%M:%S"),
                     loggable)
    f.write(msg)
    f.close()


write_testlog._passcount = 0
write_testlog._failcount = 0
