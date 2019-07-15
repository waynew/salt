from zmq.eventloop import ioloop
import salt.transport.client

opts = {
    'pki_dir': '/tmp',
    'id': 'leaky-minion',
    'keysize': 2048,
    'master_uri': 'tcp://127.0.0.1:5151',
    '__role': 'minion',
    'transport': 'zeromq',
}

channel = salt.transport.client.ReqChannel.factory(opts)
channel.asynchronous.crypt = 'clear'
print(channel)
print('sending a thing')
#breakpoint()
channel.send({'id': 42, 'cmd': 'whatever', 'data': 'howdy howdy howdy'}, timeout=5)
print('le sent')
