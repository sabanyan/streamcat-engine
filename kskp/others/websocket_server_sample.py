# sudo pip install git+https://github.com/Pithikos/python-websocket-server

import time
import logging
from websocket_server import WebsocketServer

start_time = time.time()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(' %(module)s -  %(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


# Callback functions
def new_client(client, server):
    logger.info('New client {}:{} has joined.'.format(client['address'][0], client['address'][1]))

def client_left(client, server):
    logger.info('Client {}:{} has left.'.format(client['address'][0], client['address'][1]))

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

def message_received(client, server, message):
    logger.info("Message '{}' has been received from {}:{}".format(message, client['address'][0], client['address'][1]))

    # reply_message = 'Hi! ' + message

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
            server.send_message(client, reply_message)

            logger.info("Message '{}' has been sent to {}:{}".format(reply_message, client['address'][0], client['address'][1]))
        
        server.send_message(client, 'completed!')
        server.send_message(client, repr(time.time() - start_time))


# Main
if __name__ == '__main__':
    # server = WebsocketServer(port=13254, host='127.0.0.1', loglevel=logging.INFO)
    server = WebsocketServer(port=9000, host='127.0.0.1')
    server.set_fn_new_client(new_client)
    server.set_fn_client_left(client_left)
    server.set_fn_message_received(message_received)
    server.run_forever()
