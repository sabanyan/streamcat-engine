import asyncio
import websockets

def do_something(first_pow):
    i = 0
    for n in range(2 ** first_pow):
        i += n
    # try:
    #     i = i / 0
    # except Exception as e:
    #     ex =  ValueError(f'first_pow: {first_pow}')
    #     ex.__cause__ = e
    #     return ex
    return i   

async def echo(websocket, path):
    async for message in websocket:
        # await websocket.send(message)

        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor() as executor:
            # 並行処理する対象とそれに対応する値 (処理の引数) を辞書で用意する
            mappings = {executor.submit(do_something, n): n for n in [28, 26, 24, 22]}

            # futures.as_completed() は処理がおわったものから結果を返していくジェネレータ
            for future in as_completed(mappings):
                # 完了した処理に対応する引数を辞書から取得する
                target = mappings[future]
                # 処理結果を取得する
                result = future.result()
                # 結果を表示する
                msg = '{n}: {prime}'.format(n=target, prime=result)
                # print(msg)
                reply_message = repr(msg)
                await websocket.send(reply_message)

                # logger.info("Message '{}' has been sent to {}:{}".format(reply_message, client['address'][0], client['address'][1]))
                        
            # await websocket.send('completed!')
            await websocket.send(repr(time.time() - start_time))

asyncio.get_event_loop().run_until_complete(websockets.serve(echo, 'localhost', 9000))
asyncio.get_event_loop().run_forever()