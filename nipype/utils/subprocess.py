# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Miscellaneous utility functions
"""
import os
import sys
import gc
import errno
import select
import locale
import datetime
from pathlib import Path
from subprocess import Popen, STDOUT, PIPE
from .filemanip import canonicalize_env, read_stream

from .. import logging

iflogger = logging.getLogger("nipype.interface")


class Stream(object):
    """Function to capture stdout and stderr streams with timestamps

    stackoverflow.com/questions/4984549/merge-and-sync-stdout-and-stderr/5188359
    """

    def __init__(self, name, impl):
        self._name = name
        self._impl = impl
        self._buf = ""
        self._rows = []
        self._lastidx = 0
        self.default_encoding = locale.getdefaultlocale()[1] or "UTF-8"

    def fileno(self):
        "Pass-through for file descriptor."
        return self._impl.fileno()

    def read(self, drain=0):
        "Read from the file descriptor. If 'drain' set, read until EOF."
        while self._read(drain) is not None:
            if not drain:
                break

    def _read(self, drain):
        "Read from the file descriptor"
        fd = self.fileno()
        buf = os.read(fd, 4096).decode(self.default_encoding)
        if not buf and not self._buf:
            return None
        if "\n" not in buf:
            if not drain:
                self._buf += buf
                return []

        # prepend any data previously read, then split into lines and format
        buf = self._buf + buf
        if "\n" in buf:
            tmp, rest = buf.rsplit("\n", 1)
        else:
            tmp = buf
            rest = None
        self._buf = rest
        now = datetime.datetime.now().isoformat()
        rows = tmp.split("\n")
        self._rows += [(now, "%s %s:%s" % (self._name, now, r), r) for r in rows]
        for idx in range(self._lastidx, len(self._rows)):
            iflogger.info(self._rows[idx][1])
        self._lastidx = len(self._rows)


def run_command(runtime, output=None, timeout=0.01, write_cmdline=False):
    """Run a command, read stdout and stderr, prefix with timestamp.

    The returned runtime contains a merged stdout+stderr log with timestamps
    """

    # Init variables
    cmdline = runtime.cmdline
    env = canonicalize_env(runtime.environ)

    errfile = None
    outfile = None
    stdout = PIPE
    stderr = PIPE

    if output == "file":
        outfile = os.path.join(runtime.cwd, "output.nipype")
        stdout = open(outfile, "wb")  # t=='text'===default
        stderr = STDOUT
    elif output == "file_split":
        outfile = os.path.join(runtime.cwd, "stdout.nipype")
        stdout = open(outfile, "wb")
        errfile = os.path.join(runtime.cwd, "stderr.nipype")
        stderr = open(errfile, "wb")
    elif output == "file_stdout":
        outfile = os.path.join(runtime.cwd, "stdout.nipype")
        stdout = open(outfile, "wb")
    elif output == "file_stderr":
        errfile = os.path.join(runtime.cwd, "stderr.nipype")
        stderr = open(errfile, "wb")

    if write_cmdline:
        (Path(runtime.cwd) / "command.txt").write_text(cmdline, encoding='utf-8')

    proc = Popen(
        cmdline,
        stdout=stdout,
        stderr=stderr,
        shell=True,
        cwd=runtime.cwd,
        env=env,
        close_fds=(not sys.platform.startswith("win")),
    )

    result = {
        "stdout": [],
        "stderr": [],
        "merged": [],
    }

    if output == "stream":
        streams = [Stream("stdout", proc.stdout), Stream("stderr", proc.stderr)]

        def _process(drain=0):
            try:
                res = select.select(streams, [], [], timeout)
            except select.error as e:
                iflogger.info(e)
                if e.errno == errno.EINTR:
                    return
                else:
                    raise
            else:
                for stream in res[0]:
                    stream.read(drain)

        while proc.returncode is None:
            proc.poll()
            _process()

        _process(drain=1)

        # collect results, merge and return
        result = {}
        temp = []
        for stream in streams:
            rows = stream._rows
            temp += rows
            result[stream._name] = [r[2] for r in rows]
        temp.sort()
        result["merged"] = [r[1] for r in temp]

    if output.startswith("file"):
        proc.wait()
        if outfile is not None:
            stdout.flush()
            stdout.close()
            with open(outfile, "rb") as ofh:
                stdoutstr = ofh.read()
            result["stdout"] = read_stream(stdoutstr, logger=iflogger)
            del stdoutstr

        if errfile is not None:
            stderr.flush()
            stderr.close()
            with open(errfile, "rb") as efh:
                stderrstr = efh.read()
            result["stderr"] = read_stream(stderrstr, logger=iflogger)
            del stderrstr

        if output == "file":
            result["merged"] = result["stdout"]
            result["stdout"] = []
    else:
        stdout, stderr = proc.communicate()
        if output == "allatonce":  # Discard stdout and stderr otherwise
            result["stdout"] = read_stream(stdout, logger=iflogger)
            result["stderr"] = read_stream(stderr, logger=iflogger)

    runtime.returncode = proc.returncode
    try:
        proc.terminate()  # Ensure we are done
    except OSError as error:
        # Python 2 raises when the process is already gone
        if error.errno != errno.ESRCH:
            raise

    # Dereference & force GC for a cleanup
    del proc
    del stdout
    del stderr
    gc.collect()

    runtime.stderr = "\n".join(result["stderr"])
    runtime.stdout = "\n".join(result["stdout"])
    runtime.merged = "\n".join(result["merged"])
    return runtime
