#!/usr/bin/env python3

import sys
import socket
import selectors
import types

selector = selectors.DefaultSelector()
start_marker = '<>__SOF__<>'
end_marker = '<>__EOF__<>'
read_size = 1024
char_type = 'utf-8'
sent = b''

def close_connection(key):
    print("closing connection to", key.data.addr, key.data.outb.decode(char_type))
    selector.unregister(key.fileobj)
    key.fileobj.shutdown(1)
    key.fileobj.close()
    key.data.inb = key.data.outb
    key.data.outb = None
    key.data.inb = None


def accept(socket):
    connection, address = socket.accept()
    print("connection from => ", address)
    connection.setblocking(False)
    data = types.SimpleNamespace(addr=address, inb=sent, outb=sent)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    selector.register(connection, events, data=data)

def service(key, mask):
    socket = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
       request = socket.recv(read_size)
       if  request:
           data.inb += request
       else:
           close_connection(key)


def response(socket, data):
   try:
       sent = socket.send(data.outb)
       data.outb = data.outb[sent:]
       data.inb = data.inb[sent:]
   except:
       pass

def parse_request(request):
    start = request.find(start_marker) + len(start_marker)
    end = request.find(end_marker)
    return request[start:end]

def process_request(key):
    request = parse_request(key.data.inb.decode(char_type))
    print('Request:', request)
    key.data.inb = sent
    key.data.outb = 'OK\n'.encode()
    response(key.fileobj, key.data)

def check_inputs():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

def init_server():
    print("Starting server")
    host, port = sys.argv[1], int(sys.argv[2])
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    print("listening on", (host, port))
    lsock.setblocking(False)
    selector.register(lsock, selectors.EVENT_READ, data=None)

def serve():
    try:
        while True:
            serve_events(selector.select(timeout=None))
    except:
        print("interrupted => exiting")
    finally:
        selector.close()

def serve_events(events):
    for key, mask in events:
        if key.data is None:
            accept(key.fileobj)
        elif key.data.inb is not None and end_marker in key.data.inb.decode(char_type):
            process_request(key)
            close_connection(key)
        else:
            service(key, mask)

check_inputs()
init_server()
serve()
