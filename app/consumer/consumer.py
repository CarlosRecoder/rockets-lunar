from kafka import KafkaConsumer
from kafka.errors import KafkaError
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.json_util import loads
from typing import Optional
import logging

class RocketsConsumer:

    def __init__(
            self,
            kafka_consumer: Optional[KafkaConsumer] = None,
            mongo_client: Optional[MongoClient] = None
    ):
        # Initialize the logger, the Kafka consumer, and the MongoDB client & database
        self.logger = self.setup_logger()
        self.consumer = self.initialize_kafka_consumer(kafka_consumer)
        self.mongo_client, self.db = self.initialize_mongo_client(mongo_client)

    def setup_logger(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger

    def initialize_kafka_consumer(self, kafka_consumer=None):
        # Consumer for main app
        if kafka_consumer is None:
            kafka_bootstrap_servers = 'kafka:9092'
            kafka_topic = 'rocket_messages'
            consumer_group_id = 'mongo_consumer'
            try:
                return KafkaConsumer(
                    kafka_topic,
                    bootstrap_servers=kafka_bootstrap_servers,
                    api_version=(3,4,0),
                    group_id=consumer_group_id
                )
            except KafkaError:
                self.logger.exception("Unable to connect to Kafka server")
        # Consumer for testing
        else:
            return kafka_consumer

    def initialize_mongo_client(self, mongo_client=None):
        mongodb_database = 'rocket_data'
        # MongoDB for main app
        if mongo_client is None:
            mongodb_uri = 'mongodb://mongodb:27017'
            try:
                mongo_client = MongoClient(mongodb_uri)
                return mongo_client, mongo_client[mongodb_database]
            except PyMongoError:
                self.logger.exception("Unable to connect to MongoDB server")
        # MongoDB for testing
        else:
            return mongo_client, mongo_client[mongodb_database]


    def process_message(self, message):

        try:
            # Decode the message value
            decoded_message = message.value.decode('utf-8')

            # Deserialize the message from JSON to a Python object
            rocket_message = loads(decoded_message)

        except (UnicodeDecodeError, ValueError):
            self.logger.exception('Error decoding or deserializing message:')
            return
    
        try:
            # Extract the necessary information from the rocket message
            metadata = rocket_message['metadata']
            message_time = metadata['messageTime']
            message_type = metadata['messageType']
            message_number = metadata['messageNumber']
            channel = metadata['channel']

            # Check if the channel already exists in the database
            existing_channel = self.db.rocket_channels.find_one({'channel': channel})

            if not existing_channel:
                # Create a new channel document if it doesn't exist
                self.db.rocket_channels.insert_one({'channel': channel, 'messages': []})

            # Check if the message already exists in the channel
            existing_message = self.db.rocket_channels.find_one({
                'channel': channel,
                'messages.metadata.messageNumber': message_number
            })

            if existing_message:
                # Skip the duplicate message
                self.logger.info(f"Duplicate message {message_number} on channel {channel} skipped")
                return

            # Construct the message document
            message_doc = {
                'metadata': {
                    'messageNumber': message_number,
                    'messageTime': message_time,
                    'messageType': message_type
                },
                'message': rocket_message['message']
            }

            # Append the message to the channel's messages array
            self.db.rocket_channels.update_one(
                {'channel': channel},
                {'$push': {'messages': message_doc}}
            )

            # Commit the offset to mark the message as processed
            self.consumer.commit()
            self.logger.info(f"New message {message_number} on channel {channel} committed into the database")

        except PyMongoError:
            self.logger.exception('MongoDB operation failed:')

        except KafkaError:
            self.logger.exception('Kafka operation failed:')


    def consume_messages(self):
        # Loop over messages and consume them
        for message in self.consumer:
            self.process_message(message)


if __name__ == '__main__':
    consumer_manager = RocketsConsumer()
    consumer_manager.consume_messages()