import os
import sys
import time
import asyncio
from pathlib import Path

from quart import Quart, websocket

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


app = Quart(__name__)
loop = asyncio.get_event_loop()

async def on_created_async(event):
    print('on_created:', event)
    await websocket.send('on_created:', event)

async def on_modified_async(event):
    print('on_modified:', event)
    await websocket.send('on_modified:', event)

class MyHandler(PatternMatchingEventHandler):
    def on_created(self, event):
        print('on_created:', event)
        asyncio.new_event_loop().run_until_complete(on_created_async(event))
        # loop.call_soon(on_created_async, event)

    def on_modified(self, event):
        print('on_modified:', event)
        asyncio.new_event_loop().run_until_complete(on_modified_async(event))        
        # loop.call_soon(on_modified_async, event)

observer = Observer()

@app.websocket('/ws')
async def ws():
    watch()
    while True:
        data = await websocket.receive()
        if data == 'quit':
            await websocket.send('quit')
            observer.stop()
            break
        else:            
            await websocket.send(f'you send {data}. thanx.')
            with open('kskp/others/test.txt', 'w') as f: 
                f.write(data)

def watch():
    event_handler = MyHandler()
    observer.schedule(event_handler, 'kskp/others/')
    observer.start()


if __name__ == '__main__':
    # app.run()
    with open('kskp/others/stderr.txt', 'r') as f:
        def a():            
            # print(sys.stderr.read())
            loop.remove_reader(f)
            # loop.stop()

        loop.add_reader(f, a)
        # loop.run_forever()

        # print(f.read())

        # loop.close()
    