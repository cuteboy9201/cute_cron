import pika
import logging
from pika.adapters.tornado_connection import TornadoConnection
import uuid

LOG = logging.getLogger(__name__)


class PikaPublisher(object):

    # EXCHANGE = "cron_pub_exchange"
    # QUEUE = "cron_pub_queue"
    EXCHANGE_TYPE = "topic"

    def __init__(self,
                 io_loop,
                 amqp_url="",
                 exchange="",
                 queue="",
                 routing_key=""):
        self.IO_LOOP = io_loop
        self.EXCHANGE = exchange or "default_exchange"
        self.QUEUE = queue or "default_queue"
        self.URL = amqp_url
        self.ROUTING_KEY = routing_key or "default.routing_key"

        self._connection = None
        self._channel = None
        self._acked = None
        self._nacked = None
        self._closing = False
        self._consumer_tag = None

    def connect(self):
        self._connection = TornadoConnection(
            parameters=pika.URLParameters(self.URL),
            on_open_error_callback="",
            on_open_callback=self.on_connection_open,
            on_close_callback="")

    def on_connection_open(self, _unused_connection):
        self.open_channel()

    def on_connection_open_error(self, _unused_connection, err):
        LOG.warning("connection rabbitmq err: %s", err)
        self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def on_connection_closed(self, _unused_connection, reason):
        self._channel = None
        if self._closing:
            self.IO_LOOP.stop()
        else:
            LOG.warning("connection close, reopening in 5 seconds: %s", reason)
            self._connection.ioloop.call_later(5, self._connection.ioloop.stop)

    def open_channel(self):
        LOG.info("Create a new channel")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        LOG.info("open channel")
        self._channel = channel
        self.add_on_channel_close_callback()
        self.set_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reason):
        self._connection.close()

    def set_exchange(self, exchange_name):
        LOG.info("Declaring exchange %s", exchange_name)
        self._channel.exchange_declare(exchange=exchange_name,
                                       exchange_type=self.EXCHANGE_TYPE,
                                       callback=self.on_exchange_declareok)

    def on_exchange_declareok(self, unused_frame):
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        LOG.info("Declaring queue: %s", queue_name)
        self._channel.queue_declare(callback=self.on_queue_declareok,
                                    queue=queue_name)

    def on_queue_declareok(self, unused_frame):
        LOG.info("Binding %s to %s with %s", self.EXCHANGE, self.QUEUE,
                 self.ROUTING_KEY)
        # self._channel.queue_bind(callback=self.on_bindok,
        #                          queue=self.QUEUE,
        #                          exchange=self.EXCHANGE,
        #                          routing_key=self.ROUTING_KEY)
        self._channel.queue_bind(queue=self.QUEUE,
                                 exchange=self.EXCHANGE,
                                 routing_key=self.ROUTING_KEY,
                                 callback=self.on_bindok)

    def on_bindok(self, unused_frame):
        self.start_consuming()

    def start_consuming(self):
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(
            on_message_callback=self.on_response, queue=self.QUEUE)

    def add_on_cancel_callback(self):
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, unused_frame):
        if self._channel:
            self._channel.close()

    def acknowledge_message(self, delivery_tag):
        self._channel.basic_ack(delivery_tag)

    def send_msg(self, n):
        print("start send msg")
        self.response = None
        if self._channel is None or not self._channel.is_open:
            return False
        properties = pika.BasicProperties(reply_to=self.ROUTING_KEY,
                                          correlation_id="youshumin2019")

        OK = self._channel.basic_publish(exchange="cute2",
                                         routing_key="cute.cron",
                                         body=str(n),
                                         properties=properties)
        print(OK)
        return self.response

    def on_response(self, channel, basic_deliver, properties, body):
        LOG.info("body: %s, channel: %s, properties_id: %s", body, channel,
                 properties.correlation_id)
        self.acknowledge_message(basic_deliver.delivery_tag)
        self.response = "ok"