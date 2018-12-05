import sys
from pathlib import Path

from flask import Flask, request, render_template
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

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
    def __init__(self, ws):
        super().__init__()        
        self.ws = ws

    def on_created(self, event):
        print('on_created:', event)        
        if Path(event.src_path).is_dir():
            return

    def on_modified(self, event):
        print('on_modified:', event)
        # if 'stderr' in event.src_path:            
        if Path(event.src_path).is_dir():
            return

        with open(event.src_path, 'r') as f:
            self.ws.send(f.read())


app = Flask(__name__)

observer = Observer()
event_handler = None

@app.route('/ws')
def pipe():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']        
        event_handler = MyHandler(ws)
        watch(event_handler)
        while True:
            message = ws.receive()
            ws.send(f'you send {message}. thanx.')
            execute(ws)

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

def execute(ws):
    ws.send('start_executing')
    f = None
    f <<= nm.mcut(i='kskp/data/sample.csv', x=True, f='0,1,2,3,4')
    f <<= nm.runfunc(interrupt, a='a')
    f <<= nm.mcut(x=True, f='0,1,2,3,4')
    f <<= nm.runfunc(interrupt, a='b')
    f <<= nm.mcut(x=True, f='0,1,2,3')
    f <<= nm.runfunc(interrupt, a='c')
    f <<= nm.mcut(x=True, f='0,1,2')
    f <<= nm.runfunc(interrupt, a='d')
    f <<= nm.mcut(x=True, f='0,1', o='kskp/data/result.csv')
    f <<= nm.runfunc(interrupt, a='e')
    f.run(msg='on')

def main():
    app.debug = True
    server = pywsgi.WSGIServer(("", 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()


def watch(handler):
    observer.schedule(handler, 'kskp/messages/')    
    observer.start()


if __name__ == "__main__":
    main()