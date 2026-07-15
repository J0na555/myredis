import selectors
import socket

# creating the best event notification system
# linux-> epoll, macos -> kqueue, windows -> select
sel = selectors.DefaultSelector()


class Client:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.read_buf = b""   # unparsed bytes received so far
        self.write_buf = b""   # response bytes waiting to be sent


def accept_connection(sock):
    # Called when the server socket is readable
    conn, addr = sock.accept()
    conn.setblocking(False)  # no data return anyway
    # creating a client based on the client class(did i have to say that tho)
    client = Client(conn, addr)
    # wakeup when the socket is readable
    sel.register(conn, selectors.EVENT_READ, data=client)
    print(f"connected: {addr}")


def handle_read(key):
    client = key.data
    conn = client.conn
    try:
        data = conn.recv(4096)
    except BlockingIOError:  # even tho epoll is saying readable the connection is a bitch so things might change so better be safe that sorry
        return

    if not data:
        # Empty recv means the client is disconnected
        sel.unregister(conn)
        conn.close()
        print(f"disconnected: {client.addr}")
        return

    client.read_buf += data
    # TODO: parse complete RESP commands out of client.read_buf
    # For now, just echo back to prove the loop works
    client.write_buf += data
    sel.modify(
        conn,
        selectors.EVENT_READ | selectors.EVENT_WRITE,
        data=client
    )


def handle_write(key):
    client = key.data
    conn = client.conn

    if client.write_buf:
        # send upto a certain number not all data in the buffer
        sent = conn.send(client.write_buf)
        # sends the rest that wasnot sent before
        client.write_buf = client.write_buf[sent:]
    # if we done writing then we stop cause empty socket are always writable
    if not client.write_buf:
        sel.modify(conn, selectors.EVENT_READ, data=client)


def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # this is to avoid conflict with redis port 6379
    server_sock.bind(("127.0.0.1", 6380))
    server_sock.listen()
    server_sock.setblocking(False)
    sel.register(server_sock, selectors.EVENT_READ, data=None)
    print("listening on 6380")

    # the even loop
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_connection(key.fileobj)  # if nothing accept some nigga
            else:
                if mask & selectors.EVENT_READ:
                    handle_read(key)
                if mask & selectors.EVENT_WRITE:
                    handle_write(key)


if __name__ == "__main__":
    main()

"""
 the entire loop
            +----------------------+
            |   wait in select()   |
            +----------+-----------+
                       |
          kernel reports ready sockets
                       |
        +--------------+---------------+
        |                              |
   new connection                 existing client
        |                              |
      accept()                   recv()/send()
        |                              |
   register socket             update buffers
        |                              |
        +--------------+---------------+
                       |
                  back to select()
"""
