# -*- DISCLAIMER: this file contains code derived from gputil (https://github.com/anderskm/gputil)
# and therefore is distributed under to the following license:
#
# MIT License
#
# Copyright (c) 2017 anderskm
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import platform
import shutil
import subprocess
import os


def gpu_count():
    nvidia_smi = shutil.which('nvidia-smi')
    if nvidia_smi is None and platform.system() == "Windows":
        nvidia_smi = f'{os.environ["systemdrive"]}\\Program Files\\NVIDIA Corporation\\NVSMI\\nvidia-smi.exe'
    if nvidia_smi is None:
        return 0
    try:
        p = subprocess.run(
            [nvidia_smi, "--query-gpu=name", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            text=True,
        )
    except (OSError, UnicodeDecodeError):
        return 0
    return len(p.stdout.splitlines())
