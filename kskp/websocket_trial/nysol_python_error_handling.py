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

if __name__ == '__main__':

    def bigAmount0():
        f = None
        # f <<= nm.mstdin()
        # f <<= nm.mcut(i='kskp/others/sample.csv', x=True, f='0,1,2,3,4', o='kskp/others/sample1.csv')
        f <<= nm.mcut(i='kskp/others/sample.csv', x=True, f='0,1,2,3,4')
        f <<= nm.mstdout()
        with RedirectStdStreams(stderr=open('kskp/others/stderr0.txt','w')):
            f.run(msg='on')
            sys.stderr.flush()

    def bigAmount1():
        f = None
        f <<= nm.mstdin()
        # f <<= nm.mcut(x=True, f='0,1,2,3', o='kskp/others/sample2.csv')
        f <<= nm.mcut(x=True, f='0,1,2,3')
        f <<= nm.mstdout()
        with RedirectStdStreams(stderr=open('kskp/others/stderr1.txt','w')):
            f.run(msg='on')
            sys.stderr.flush()

    def bigAmount2():
        f = None
        f <<= nm.mstdin()
        # f <<= nm.mcut(x=True, f='0,1,2', o='kskp/others/sample3.csv')
        f <<= nm.mcut(x=True, f='0,1,2')
        f <<= nm.mstdout()
        with RedirectStdStreams(stderr=open('kskp/others/stderr2.txt','w')):
            f.run(msg='on')
            sys.stderr.flush()

    def bigAmount3():
        f = None
        f <<= nm.mstdin()
        # f <<= nm.mcut(x=True, f='0,1', o='kskp/others/sample3.csv')
        f <<= nm.mcut(x=True, f='0,1')
        f <<= nm.mstdout()
        with RedirectStdStreams(stderr=open('kskp/others/stderr3.txt','w')):
            f.run(msg='on')
            sys.stderr.flush()

    # with RedirectStdStreams(stderr=open('kskp/others/stderr.txt','w')):
    a = None
    a <<= nm.runfunc(bigAmount0)
    a <<= nm.runfunc(bigAmount1)
    a <<= nm.runfunc(bigAmount2)
    a <<= nm.runfunc(bigAmount3)
    a.run()
