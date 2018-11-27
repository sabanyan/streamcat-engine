import asyncio
import time

from kskp.store import Command
import kskp.engine as engine
from kskp.engine import Flow, Arrow, Step, Port

# from flask import Flask
from quart import Quart, websocket

loop = asyncio.get_event_loop()
app = Quart(__name__)

@app.websocket('/ws')
async def ws():    
    while True:
        data = await websocket.receive()
        await websocket.send(f'you send {data}')
        # start_time = time.time()        
        await execute_by_engine()

async def execute_by_engine():
    print('wowow')
    await websocket.send('wowow')

    class TestCommand(Command):
        def __init__(self):
            super().__init__()
            # self.i_ports = [Port('i', '')]
            self.o_ports = [Port('o', '')]

        def run(self, args, inputs):            
            start_time = time.time()
            results = echo2(start_time)
            print('results:', results)
            return {'o': results}

    class EmptyLink:
        def resolve(self):
            flow = Flow()
            # flow.o_ports = [Port('o', '')] # lastsをもらうだけなので親flowのportは関係ない
            step = Step('s', TestCommand(), {})
            flow.substeps = [step]
            # flow.arrows = [Arrow('in', None, None, None, step.runnable.i_ports[0], step),
            #                Arrow('out', step, step.runnable.o_ports[0], None, None, None)]
            # flow.arrows = [Arrow('out', step, step.runnable.o_ports[0], None, flow.o_ports[0], None)]
            flow.arrows = [Arrow('out', step, step.runnable.o_ports[0], None, None, None)]
            return flow

    result = engine.execute(EmptyLink(), {}, {})
    await websocket.send(f'result: {repr(result)}')
    await websocket.send('popop')

def echo2(start_time):
    from concurrent.futures import ProcessPoolExecutor, as_completed

    with ProcessPoolExecutor() as executor:
        # 並行処理する対象とそれに対応する値 (処理の引数) を辞書で用意する
        mappings = {executor.submit(do_something, n): n for n in [28, 26, 24, 22]}
        # mappings = executor.map(do_something, [28, 26, 24, 22])

        results = []
        # print('mappings:', mappings)
        # futures.as_completed() は処理がおわったものから結果を返していくジェネレータ
        for future in as_completed(mappings):
        # for future in mappings:
            # 完了した処理に対応する引数を辞書から取得する
            target = mappings[future]
            # print(repr(future))
            # target = future


            # 処理結果を取得する

            try:
                # ex = future.exception()
                # if ex is not None:
                #     print('exception by do_something:', ex, future.cancelled())                
                # else:
                #     print('ex is None')

                result = future.result()

                # 結果を表示する
                msg = '{n}: {prime}'.format(n=target, prime=result)
                # print(msg)
                reply_message = repr(msg)            
                results.append(reply_message)
                print(reply_message)
                # logger.info("Message '{}' has been sent to {}:{}".format(reply_message, client['address'][0], client['address'][1])) 

            except Exception as e:
                print('exception by do_something:', e)
                results.append(repr(e))
        
        return results

def do_something(first_pow):
    i = 0
    for n in range(2 ** first_pow):
        i += n        

        # raise ValueError(f'value: {first_pow}')

    # try:
    #     i = i / 0
    # except Exception as e:
    #     ex = ValueError(f'first_pow: {first_pow}')
    #     ex.__cause__ = e
    #     # return ex
    #     raise ex from e

    return i   


app.run()