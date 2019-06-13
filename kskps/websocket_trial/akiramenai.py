import sys
import importlib
from pathlib import Path

from flask import Flask, request, render_template
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from watchdog.events import PatternMatchingEventHandler

import nysol.mcmd as nm

from kskps.store import Command, Port, Parameter
import kskps.engine
from kskps.engine import Flow, Step, Point, Job


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
        self.send_message(event)

    def on_modified(self, event):
        print('on_modified:', event)
        self.send_message(event)
    
    def send_message(self, event):
        if event.is_directory:
            return 

        with open(event.src_path, 'r') as f:
            self.ws.send(f'{f.read()} is done!')


class Mcut(Command):
    def __init__(self):
        super().__init__()
        self.i_ports = [Port('i', 'nm')] # nmは仮
        self.o_ports = [Port('o', 'nm')] # nmは仮
        self.params = [Parameter('f', '列名')]
    
    def run(self, args, inputs):
        print('running mcut args:', args)
        f = None
        # print('mcut f:', f)
        f <<= nm.mcut(i=inputs['i'], x=True, f=args['f'])
        # print('mcut f:', f)
        f <<= nm.runfunc(interrupt, a=self.context['step_id'])
        # print('mcut f:', f)
        return {'o': f}

# class TestCommand(Command):
#     def run(self, args, inputs):
#         f = None
#         f <<= nm.mcut(i='kskp/data/sample.csv', x=True, f='0,1,2,3,4')
#         f <<= nm.runfunc(interrupt, a='a')
#         f <<= nm.mcut(x=True, f='0,1,2,3,4')
#         f <<= nm.runfunc(interrupt, a='b')
#         f <<= nm.mcut(x=True, f='0,1,2,3')
#         f <<= nm.runfunc(interrupt, a='c')
#         f <<= nm.mcut(x=True, f='0,1,2')
#         f <<= nm.runfunc(interrupt, a='d')
#         f <<= nm.mcut(x=True, f='0,1', o='kskp/data/result.csv')
#         f <<= nm.runfunc(interrupt, a='e')
        
#         return {'o': f.run(msg='on')}

class TestLink:
    def resolve(self):
        flow = Flow()       

        step1 = Step('s1', Mcut(), {'f': '0,1,2,3,4'})
        step2 = Step('s2', Mcut(), {'f': '0,1,2,3'})
                        
        flow.substeps = [step1, step2]
        flow.points = [Point('d1', None, None, 'kskp/data/sample.csv', step1.runnable.i_ports[0], step1),
                       Point('d2', step1, step1.runnable.o_ports[0], None, step2.runnable.i_ports[0], step2),
                       Point('d3', step2, step2.runnable.o_ports[0], None, None, None)]
        
        return flow


app = Flask(__name__)


@app.route('/execute')
def try_to_execute():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']        

        while True:
            message = ws.receive()
            ws.send(f'you send {message}. thanx.')
            result = kskps.engine.execute(TestLink(), {}, {}, job_complete_handler=MyHandler(ws))            
            print('result:', result)

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

def main():
    app.debug = True
    server = pywsgi.WSGIServer(("", 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
