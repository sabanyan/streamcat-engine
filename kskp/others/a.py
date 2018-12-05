import os
import sys

import nysol.mcmd as nm

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

f = None
f <<= nm.mcut(i='kskp/others/sample.csv', x=True, f='0,1,2,3,4')
# f <<= nm.mstdout()
with RedirectStdStreams(stderr=open('kskp/others/stderr.txt','w')):
    f.run(msg='on')