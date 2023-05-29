from fastapi import FastAPI
from pydantic import BaseModel
from kafka import KafkaProducer
import uvicorn

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

# API endpoint for receiving rocket messages
@app.post('/messages')
def receive_message(message: RocketMessage):
    # Publish the message to the Kafka topic
    producer.send(kafka_topic, value=message.json().encode('utf-8'))

    return 'Message received and published to Kafka'

# Run the FastAPI application
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8088)