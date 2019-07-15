import logging
import salt.transport.server
import salt.utils.asynchronous
import salt.utils.process
import time
import zmq

logging.basicConfig(level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s')


def try_one():
    io_loop = salt.utils.asynchronous.tornado.ioloop.IOLoop()

    process_manager = salt.utils.process.ProcessManager(wait_for_kill=5)
    opts = {
        'ipv6': False,
        'interface': '127.0.0.1',
        'publish_port': 5151,
        'sock_dir': '/tmp/',
        'transport': 'zeromq',
    }

    chan = salt.transport.server.PubServerChannel.factory(opts)
    chan.pre_fork(process_manager)

def try_two():
    ctx = zmq.Context()
    socket = ctx.socket(zmq.REP)
    socket.bind('tcp://127.0.0.1:5151')

    while True:
        msg = socket.recv()
        print('Got le msg', msg)
        time.sleep(1)
        print('sending response')
        socket.send(b"Cool deal")
        print('it was sent')


if __name__ == '__main__':
    try_two()
