import asyncio
import time

from kskp.core import Command
import kskp.engine as engine
from kskp.engine import Flow, Point, Step, Port

# from flask import Flask
from quart import Quart, websocket

loop = asyncio.get_event_loop()
app = Quart(__name__)

@app.websocket('/ws')
async def ws():    
    while True:
        data = await websocket.receive()
        await websocket.send(f'you send {data}')        
        await execute_by_engine()

async def execute_dummy():
    """ generatorで返したい """
    for e in echo_generator(time.time()):
        await websocket.send(repr(e))

async def execute_by_engine():
    print('start executing')
    await websocket.send('start executing')

    class TestCommand(Command):
        def __init__(self):
            super().__init__()
            # self.i_ports = [Port('i', '')]
            self.o_ports = [Port('o', '')]

        def run(self, args, inputs):            
            start_time = time.time()
            results = do_something(start_time)
            print('results:', results)
            return {'o': results}

    class EmptyLink:
        def resolve(self):
            flow = Flow()
            
            step = Step('s', TestCommand(), {})

            flow.substeps = [step]

            flow.points = [Point('out', step, step.runnable.o_ports[0], None, None, None)]

            return flow

    result = engine.execute(EmptyLink(), {}, {})
    await websocket.send(f'result: {repr(result)}')
    print('end executing')

def echo_generator(start_time):
    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor() as executor:
        # 並行処理する対象とそれに対応する値 (処理の引数) を辞書で用意する
        mappings = {executor.submit(do_something, n): n for n in [28, 26, 24, 22]}        

        results = []

        # futures.as_completed() は処理がおわったものから結果を返していくジェネレータ
        for future in as_completed(mappings):
            # 完了した処理に対応する引数を辞書から取得する
            target = mappings[future]

            # 処理結果を取得する
            try:
                result = future.result()

                # 結果を表示する
                msg = '{n}: {prime}'.format(n=target, prime=result)
                reply_message = repr(msg)            
                print(reply_message)
                yield reply_message

            except Exception as e:
                print('exception by do_something:', e)
                yield repr(e)
        
        return results

def do_something(first_pow):
    i = 0
    for n in range(2 ** first_pow):
        i += n        
        # raise ValueError(f'value: {first_pow}')
    return i   


app.run()