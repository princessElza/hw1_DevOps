"""Kafka Consumer для результатов классификации изображений."""
import json
import os
import time

from kafka import KafkaConsumer
from src.logger import Logger


logger = Logger(True).get_logger(__name__)


def run_consumer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    topic = os.getenv("KAFKA_TOPIC", "prediction-events")

    while True:
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap_servers,
                group_id="prediction-results",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
            logger.info(f"Kafka consumer подключен к topic {topic}")
            for message in consumer:
                logger.info(f"Kafka consumer получил результат: {message.value}")
        except Exception as error:
            logger.warning(f"Kafka пока недоступна, повтор через 5 секунд: {error}")
            time.sleep(5)


if __name__ == "__main__":
    run_consumer()
