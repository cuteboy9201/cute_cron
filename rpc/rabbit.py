from oslo.task import mq_server
from oslo.task import mq_client
import pika
import logging
import uuid
LOG = logging.getLogger(__name__)


class RabbitClient(mq_client.PikaConsumer):
    def _on_message(self, channel, basic_deliver, properties, body):
        """
            作为消费者接受消息,并做处理
        """
        LOG.info("on message")

        props = pika.BasicProperties(correlation_id=properties.correlation_id)
        channel.basic_publish(exchange=properties.message_id,
                              routing_key=properties.reply_to,
                              body="sadfasdfasdfasf",
                              properties=props)
        self._acknowledge_message(basic_deliver.delivery_tag)


class RabbitServer(mq_server.PikaPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.props = pika.BasicProperties(reply_to=self.ROUTING_KEY,
                                          message_id=self.EXCHANGE)

    def handler_body(self, msg):
        """
            处理回复信息 本项目不会主动发送请求,仅测试时候使用
        """
        LOG.info("接受回复信息:{}".format(msg))
        return True