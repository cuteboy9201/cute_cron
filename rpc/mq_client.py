import pika
import logging
from pika.adapters.tornado_connection import TornadoConnection
import uuid
LOG = logging.getLogger(__name__)


class PikaConsumer(object):

    EXCHANGE = "cute2"
    EXCHANGE_TYPE = "topic"

    def __init__(self,
                 io_loop=None,
                 amqp_url="",
                 queue_name="",
                 routing_key=""):
        self._io_loop = io_loop
        self._connection = None
        self._closing = False
        self._channel = None
        self._url = amqp_url
        self._consumer_tag = None
        self.QUEUE = queue_name
        self.ROUTING_KEY = routing_key

        LOG.info("消费者绑定: 交换机{},类型{},队列名字{},路由前缀{}".format(
            self.EXCHANGE, self.EXCHANGE_TYPE, self.QUEUE, self.ROUTING_KEY))

    def connect(self):
        """连接到rabbitmq, 赋值给self._connection, 并调用self._on_connection_open方法"""
        self._connection = TornadoConnection(
            parameters=pika.URLParameters(self._url),
            on_open_callback=self._on_connection_open)

    def close_connection(self):
        self._connection.close()

    def _on_connection_open(self, unused_connection):
        """当rabbitmq被打开时, 设置基本信息"""
        self._add_on_connection_close_callback()
        self._open_channel()

    def _add_on_connection_close_callback(self):
        """当rabbitmq意外关闭与发布者的连接的时候, 调用关闭连接"""
        self._connection.add_on_close_callback(self._on_connection_closed)

    def _on_connection_closed(self, connection, reason):
        """当rabbitmq意外关闭的时候尝试重新连接"""
        self._channel = None
        if self._closing:
            self._io_loop.stop()
        else:
            LOG.warning("connection close, reopening in 5 seconds: %s", reason)
            self._connection.ioloop.call_later(5, self._reconnect)

    def _reconnect(self):
        """重新连接"""
        if not self._closing:
            self._connection = self.connect()

    def _open_channel(self):
        """发布channel, 打开一个新的rabbitmq渠道...成功的时候将调用self._on_channel_open"""
        self._connection.channel(on_open_callback=self._on_channel_open)

    def _on_channel_open(self, channel):
        """当通道打开的时候, 我们申明使用的交换信息"""
        self._channel = channel
        self._add_on_channel_close_callback()
        self._set_exchange(self.EXCHANGE)

    def _add_on_channel_close_callback(self):
        """设置通道关闭回调"""
        self._channel.add_on_close_callback(self._on_channel_closed)

    def _on_channel_closed(self, channel, reason):
        self._connection.close()

    def _set_exchange(self, exchange_name):
        LOG.info('Declaring exchange %s', exchange_name)
        self._channel.exchange_declare(callback=self._on_exchange_declareok,
                                       exchange=exchange_name,
                                       exchange_type=self.EXCHANGE_TYPE)

    def _on_exchange_declareok(self, unused_frame):
        self._setup_queue(self.QUEUE)

    def _setup_queue(self, queue_name):
        self._channel.queue_declare(callback=self._on_queue_declareok,
                                    queue=queue_name)

    def _on_queue_declareok(self, method_frame):
        self._channel.queue_bind(callback=self._on_bindok,
                                 queue=self.QUEUE,
                                 exchange=self.EXCHANGE,
                                 routing_key=self.ROUTING_KEY)

    def _on_bindok(self, unused_frame):
        self._start_consuming()

    def _start_consuming(self):
        self._add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(
            on_message_callback=self._on_message, queue=self.QUEUE)

    def _add_on_cancel_callback(self):
        self._channel.add_on_cancel_callback(self._on_consumer_cancelled)

    def _on_consumer_cancelled(self, method_frame):
        if self._channel:
            self._channel.close()

    def _on_message(self, channel, basic_deliver, properties, body):

        self._handler(channel, properties, body)
        self._acknowledge_message(basic_deliver.delivery_tag)

    def _acknowledge_message(self, delivery_tag):
        LOG.info("return client ok")
        self._channel.basic_ack(delivery_tag)

    def _cb(self, mq, props, msg, body):
        LOG.info("start call back data ---> client: %s", msg)
        LOG.info("props.correlation_id: {}".format(props.correlation_id))
        LOG.info("props.reply_to: {}".format(props.reply_to))
        LOG.info("body: {}".format(body))
        import time
        if body == b"30":
            LOG.info("body=30")
            time.sleep(30)
        elif body == b"xxx":
            LOG.info("body=xxx")
            time.sleep(10)
        else:
            LOG.info("body=None")
            time.sleep(5)
        LOG.info(props.correlation_id)
        mq.basic_publish(exchange="default_exchange",
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(
                             correlation_id=props.correlation_id),
                         body=msg)

    def _handler(self, channel, props, body):
        LOG.info("req: %s", str(body))
        self._cb(channel, props, "xxx", body)