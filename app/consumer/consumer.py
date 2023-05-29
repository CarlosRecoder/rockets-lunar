from kafka import KafkaConsumer
from kafka.errors import KafkaError
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.json_util import loads
import logging

def setup_logger():
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    logger.addHandler(c_handler)
    return logger

# Setup logger
logger = setup_logger()

# Initialize Kafka consumer
kafka_bootstrap_servers = 'kafka:9092'
kafka_topic = 'rocket_messages'
consumer_group_id = 'mongo_consumer'
try:
    consumer = KafkaConsumer(kafka_topic,
                            bootstrap_servers=kafka_bootstrap_servers,
                            api_version=(3,4,0),
                            group_id=consumer_group_id)
except KafkaError:
    logger.exception("Unable to connect to Kafka server")

# Initialize MongoDB client and database
mongodb_uri = 'mongodb://mongodb:27017'
mongodb_database = 'rocket_data'
try:
    mongo_client = MongoClient(mongodb_uri)
except PyMongoError:
    logger.exception("Unable to connect to MongoDB server")
db = mongo_client[mongodb_database]

# Data processing and storage logic
def process_message(message):

    try:
        # Decode the message value
        decoded_message = message.value.decode('utf-8')

        # Deserialize the message from JSON to a Python object
        rocket_message = loads(decoded_message)

    except (UnicodeDecodeError, ValueError):
        logger.exception('Error decoding or deserializing message:')
        return
    
    try:
        # Extract the necessary information from the rocket message
        metadata = rocket_message['metadata']
        message_time = metadata['messageTime']
        message_type = metadata['messageType']
        message_number = metadata['messageNumber']
        channel = metadata['channel']

        # Check if the channel already exists in the database
        existing_channel = db.rocket_channels.find_one({'channel': channel})

        if not existing_channel:
            # Create a new channel document if it doesn't exist
            db.rocket_channels.insert_one({'channel': channel, 'messages': []})

        # Check if the message already exists in the channel
        existing_message = db.rocket_channels.find_one({
            'channel': channel,
            'messages.metadata.messageNumber': message_number
        })

        if existing_message:
            # Skip the duplicate message
            logger.info(f"Duplicate message {message_number} on channel {channel} skipped")
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
        db.rocket_channels.update_one(
            {'channel': channel},
            {'$push': {'messages': message_doc}}
        )

        # Commit the offset to mark the message as processed
        consumer.commit()
        logger.info(f"New message {message_number} on channel {channel} committed into the database")

    except PyMongoError:
        logger.exception('MongoDB operation failed:')

    except KafkaError:
        logger.exception('Kafka operation failed:')

# Consume messages
for message in consumer:
    process_message(message)

