'''
@Author: your name
@Date: 2019-12-09 16:00:12
@LastEditTime: 2019-12-09 16:00:16
@LastEditors: Please set LastEditors
@Description: In User Settings Edit
@FilePath: /cron/test/test.py
'''
class PikaConsumer(object):
    ''' The pika client the tornado will be part of '''
 
    def __init__(self, io_loop):
        print 'PikaClient: __init__'
        self.io_loop = io_loop
        self.connected = False
        self.connecting = False
        self.connection = None
        self.channel = None
        self.event_listeners = {}
 
    def connect(self):
        ''' Connect to the broker '''
        if self.connecting:
           print 'PikaClient: Already connecting to RabbitMQ'
           return
 
        print 'PikaClient: Connecting to RabbitMQ'
        self.connecting = True
 
        cred = pika.PlainCredentials('someuser', 'somepass')
        param = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='somevhost',
            credentials=cred)
        self.connection = TornadoConnection(
                    param,
                    on_open_callback=self.on_connected)
        self.connection.add_on_close_callback(self.on_closed)
 
    def on_connected(self, connection):
        print 'PikaClient: connected to RabbitMQ'
        self.connected = True
        self.connection = connection
        self.connection.channel(self.on_channel_open)
 
    def on_channel_open(self, channel):
        print 'PikaClient: Channel open, Declaring exchange'
        self.channel = channel
        # declare exchanges, which in turn, declare
        # queues, and bind exchange to queues
        self.channel.exchange_declare(
              exchange='someexchange',
              type='topic')
        self.channel.queue_declare(self.on_queue_declare, exclusive=True)
 
    def on_queue_declare(self, result):
        queue_name = result.method.queue
        self.channel.queue_bind(
        self.on_queue_bind,
        exchange='someexchange',
        queue=queue_name,
        routing_key='commands.*')
        self.channel.basic_consume(self.on_message)
 
    def on_queue_bind(self, is_ok):
        print 'PikaClient: Exchanges and queue created/joined'
 
    def on_closed(self, connection):
        print 'PikaClient: rabbit connection closed'
        self.io_loop.stop()
 
    def on_message(self, channel, method, header, body):
        print 'PikaClient: message received: %s' % body
        self.notify_listeners(body)
        # important, since rmq needs to know that this msg is received by the
        # consumer. Otherwise, it will be overwhelmed
        channel.basic_ack(delivery_tag=method.delivery_tag)
 
    def notify_listeners(self, event_obj):
        # do whatever you wish
        pass
 
    def add_event_listener(self, listener):
        # listener.id is the box id now
        self.event_listeners[listener.id] = {
                'id': listener.id, 'obj': listener}
        print 'PikaClient: listener %s added' % repr(listener)
 
    def remove_event_listener(self, listener):
        try:
            del self.event_listeners[listener.id]
            print 'PikaClient: listener %s removed' % repr(listener)
        except KeyError:
            pass
 
    def event_listener(self, some_id):
        ''' Gives the socket object with the given some_id '''
 
        tmp_obj = self.event_listeners.get(some_id)
        if tmp_obj is not None:
            return tmp_obj['obj']
        return None