from flask.ext.aiohttp import websocket


@app.route('/hello/<name>')
@websocket
def hello(name):
    while True:
        msg = yield from aio.ws.receive_msg()

        if msg.tp == aiohttp.MsgType.text:
            aio.ws.send_str('Hello, {}'.format(name))
        elif msg.tp == aiohttp.MsgType.close:
            print('websocket connection closed')
            break
        elif msg.tp == aiohttp.MsgType.error:
            print('ws connection closed with exception %s',
                  aio.ws.exception())
            break