"""FastStream-backed RabbitMQ message publisher."""

from typing import Any

from faststream.rabbit import RabbitBroker, RabbitExchange


class FSRabbitPublisher:
    """Publishes messages to a RabbitMQ exchange via FastStream."""

    def __init__(self, broker: RabbitBroker, exchange: RabbitExchange) -> None:
        """Initialize the publisher.

        Args:
            broker: Connected FastStream RabbitBroker instance.
            exchange: Target RabbitMQ exchange.

        """
        self._broker = broker
        self._exchange = exchange

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Publish a message with the given routing key to the exchange.

        Args:
            routing_key: RabbitMQ routing key.
            payload: Message payload as a dictionary.

        """
        await self._broker.publish(
            payload,
            routing_key=routing_key,
            exchange=self._exchange,
        )
