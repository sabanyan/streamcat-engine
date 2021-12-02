from geventwebsocket import WebSocketServer, WebSocketApplication

class EchoApplication(WebSocketApplication):
    def on_open(self):
        print("Connection opened")

    def on_message(self, message):
        self.ws.send(message)

    def on_close(self, reason):
        print(reason)

def echo_app(environ, start_response):
    websocket = environ.get("wsgi.websocket")

    if websocket is None:
        return http_handler(environ, start_response)
    try:
        while True:
            message = websocket.receive()
            websocket.send(message)
        websocket.close()
    except geventwebsocket.WebSocketError as ex:
        print("{0}: {1}".format(ex.__class__.__name__, ex))

# WebSocketServer(
#     ('', 8000),
#     Resource(OrderedDict([('/', EchoApplication)]))
# ).serve_forever()

# print("Running %s from %s" % (agent, path))
WebSocketServer(("", 8000), echo_app, debug=False).serve_forever()