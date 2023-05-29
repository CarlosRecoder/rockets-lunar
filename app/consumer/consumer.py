from kafka import KafkaConsumer
from pymongo import MongoClient
from bson.json_util import loads

# Initialize Kafka consumer
kafka_bootstrap_servers = 'kafka:9092'
kafka_topic = 'rocket_messages'
consumer_group_id = 'mongo_consumer'
consumer = KafkaConsumer(kafka_topic, 
                         bootstrap_servers=kafka_bootstrap_servers, 
                         api_version=(3,4,0),
                         group_id=consumer_group_id)

# Initialize MongoDB client and database
mongodb_uri = 'mongodb://mongodb:27017'
mongodb_database = 'rocket_data'
mongo_client = MongoClient(mongodb_uri)
db = mongo_client[mongodb_database]

# Data processing and storage logic
for message in consumer:
    # Decode the message value
    decoded_message = message.value.decode('utf-8')
    
    # Deserialize the message from JSON to a Python object
    rocket_message = loads(decoded_message)
    
    # Extract the necessary information from the rocket message
    metadata = rocket_message['metadata']
    message_time = metadata['messageTime']
    message_type = metadata['messageType']
    message_number = metadata['messageNumber']
    channel = metadata['channel']

    # set channel as unique id
    db.rocket_channels.create_index('channel', unique=True)
    
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
        continue
    
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
    print("new message commited into the database")