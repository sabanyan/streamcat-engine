# server.py
from flask import Flask, request, render_template
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from werkzeug.exceptions import abort

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/echo')
def echo():
    # environ['wsgi.websocket'] から WebSocket オブジェクトが得られる
    ws = request.environ['wsgi.websocket']
    if not ws:
        abort(400)
    while True:
        # ユーザの入力
        message = ws.receive()
        # 入力をエコーバックする
        ws.send(message)


@app.route('/pipe')
def pipe():
    if request.environ.get('wsgi.websocket'):
        ws = request.environ['wsgi.websocket']

        while True:
            ws.send(input())


def main():
    app.debug = True
    server = pywsgi.WSGIServer(("", 8080), app, handler_class=WebSocketHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()