"""
コマンドの進捗やエラーが取れて、WebSocketで返してくれるやつ

サーバにあたるものが3つある
1. HTTP
2. WebSocket
3. ファイル書き込み監視
"""

import sys
import traceback
import asyncio
from pathlib import Path

from quart import Quart, websocket

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

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


class MyHandler(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__()
        self.res = None

    def on_created(self, event):
        print('on_created:', event)        
        if Path(event.src_path).is_dir():
            return
        with open(event.src_path, 'r') as f:
            f.flush()
            self.res = f.read()

    def on_modified(self, event):
        print('on_modified:', event)
        # if 'stderr' in event.src_path:            
        if Path(event.src_path).is_dir():
            return

        with open(event.src_path, 'r') as f:
            f.flush()
            self.res = f.read()


app = Quart(__name__)

observer = Observer()
event_handler = MyHandler()


@app.websocket('/ws')
async def ws():
    while True:
        data = await websocket.receive()
        await websocket.send(f'you send {data}. thanx.')
        # for g in get_stderrs():
        #     await websocket.send(f"i'll you send {g}. thanx.")
        await write_f('a')

# async def get_stderrs():    
    # yield write_f('aaa')
    # yield write_f('bbbb')
    # yield write_f('cccc')

async def write_f(s):
    bigAmount_normal()
    # with open(f'kskp/others/stderr{s}.txt', 'w') as f:
    #     f.write(s + 'g4srxfd')
    while True:
        if event_handler.res is not None:
            break
    res = event_handler.res
    event_handler.res = None
    await websocket.send(f"i'll you send {res}. thanx.")

# def bigAmount0():
#     try:
#         f = None
#         # f <<= nm.mstdin()
#         # f <<= nm.mcut(i='kskp/others/sample.csv', x=True, f='0,1,2,3,4', o='kskp/others/sample1.csv')
#         f <<= nm.mcut(i='kskp/data/sample.csv', x=True, f='0,1,2,3,4')
#         f <<= nm.mstdout()
#         with RedirectStdStreams(stderr=open('kskp/messages/stderr0.txt','w')):
#             f.run(msg='on')
#     except Exception as e:
#         with open('/dev/stderr', 'w') as fpe:
#             traceback.print_exc(file=fpe)

# def bigAmount1():
#     try:
#         f = None
#         f <<= nm.mstdin()
#         # f <<= nm.mcut(x=True, f='0,1,2,3', o='kskp/others/sample2.csv')
#         f <<= nm.mcut(x=True, f='0,1,2,3')
#         f <<= nm.mstdout()
#         with RedirectStdStreams(stderr=open('kskp/messages/stderr1.txt','w')):
#             f.run(msg='on')
#     except Exception as e:
#         with open('/dev/stderr', 'w') as fpe:
#             traceback.print_exc(file=fpe)

# def bigAmount2():
#     try:
#         f = None
#         f <<= nm.mstdin()
#         # f <<= nm.mcut(x=True, f='0,1,2', o='kskp/others/sample3.csv')
#         f <<= nm.mcut(x=True, f='0,1,2')
#         f <<= nm.mstdout()
#         with RedirectStdStreams(stderr=open('kskp/messages/stderr2.txt','w')):
#             f.run(msg='on')
#     except Exception as e:
#         with open('/dev/stderr', 'w') as fpe:
#             traceback.print_exc(file=fpe)

# def bigAmount3():
#     try:
#         f = None
#         f <<= nm.mstdin()
#         # f <<= nm.mcut(x=True, f='0,1', o='kskp/others/sample3.csv')
#         f <<= nm.mcut(x=True, f='0,1')
#         f <<= nm.mstdout()
#         with RedirectStdStreams(stderr=open('kskp/messages/stderr3.txt','w')):
#             f.run(msg='on')
#     except Exception as e:
#         with open('/dev/stderr', 'w') as fpe:
#             traceback.print_exc(file=fpe)

# def bigAmount():   
#     try:
#         # with RedirectStdStreams(stderr=open('kskp/messages/stderr.txt','w')):
#         a = None
#         a <<= nm.runfunc(bigAmount0)
#         a <<= nm.runfunc(bigAmount1)
#         a <<= nm.runfunc(bigAmount2)
#         a <<= nm.runfunc(bigAmount3, o='kskp/data/end.csv')    
#         a.run()
#     except Exception as e:
#         with open('/dev/stderr', 'w') as fpe:
#             traceback.print_exc(file=fpe)

def interrupt(a):
    header = True
    for line in sys.stdin:
        if header:
            print(line.strip())
            header = False
        else:
            tokens = line.strip().split(",")        
            print(",".join(tokens))

    with open(f'kskp/messages/stderr{a}.txt','w') as f:
        f.write(a)

    asyncio.get_event_loop().run_until_complete(websocket.send(a))

def bigAmount_normal():
    f = None
    f <<= nm.mcut(i='kskp/data/sample.csv', x=True, f='0,1,2,3,4')
    f <<= nm.runfunc(interrupt, a='a')
    f <<= nm.mcut(x=True, f='0,1,2,3')
    f <<= nm.runfunc(interrupt, a='b')
    f <<= nm.mcut(x=True, f='0,1,2')
    f <<= nm.runfunc(interrupt, a='c')
    f <<= nm.mcut(x=True, f='0,1', o='kskp/data/result.csv')
    # f <<= nm.runfunc(interrupt, a='d')
    # with RedirectStdStreams(stderr=open('kskp/messages/stderr.txt','w')):
    #     f.run(msg='on')
    f.run(msg='on')

wk = ''
def be_written():
    global wk
    with open('/dev/stderr', 'r') as f:
        a = f.read()
        f.flush()
        if a != wk:
            print(a)
            wk = a

def be_read():
    print('be read')

def be_usr1():
    print('be SIGUSR1')

import signal

def watch():
    # pass
    observer.schedule(event_handler, 'kskp/messages/')
    # observer.schedule(event_handler, '/dev')
    observer.start()

    # asyncio.get_event_loop().add_writer(open('/dev/stderr', 'w'), be_written)

    # asyncio.get_event_loop().add_writer(open('kskp/messages/stderr.txt','w'), be_read)
    # asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGPIPE'), be_read)
    # asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGINT'), be_read)
    # asyncio.get_event_loop().add_signal_handler(getattr(signal, 'SIGUSR1'), be_read)
    

if __name__ == '__main__':    
    watch()
    app.run()