from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
from kafka.errors import KafkaError
import uvicorn
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

# Define the rocket message model
class RocketMessage(BaseModel):
    metadata: dict
    message: dict

# Initialize the FastAPI application
app = FastAPI()

# Initialize the Kafka producer
kafka_bootstrap_servers = 'kafka:9092'
kafka_topic = 'rocket_messages'
producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, api_version=(3,4,0))

# Setup logger
logger = setup_logger()

# API endpoint for receiving rocket messages
@app.post('/messages')
def receive_message(message: RocketMessage):
    # Publish the message to the Kafka topic
    try:
        future = producer.send(kafka_topic, value=message.json().encode('utf-8'))
        record_metadata = future.get(timeout=10)
        logger.info('Message delivered to topic %s', record_metadata.topic)

    except KafkaError:
        logger.exception('Message delivery failed:')
        raise HTTPException(status_code=500, detail="Message delivery failed")
    
    return 'Message received and published to Kafka'

# Run the FastAPI application
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)