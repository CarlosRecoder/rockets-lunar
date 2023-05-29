from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.producer.producer import app

# Create a test client using FastAPI's TestClient
client = TestClient(app)

def test_receive_message():
    # Define a sample rocket message to be used in tests
    test_message = {
        'metadata': {'key': 'value'},
        'message': {'content': 'This is a test message'}
    }
    
    # Use patch to replace KafkaProducer.send with a Mock object
    with patch('kafka.KafkaProducer.send') as mock_send:
        # Define the behavior of the Mock object
        mock_send.return_value.get.return_value = True
        
        # Make a POST request to the /messages endpoint with the test message
        response = client.post('/messages', json=test_message)

    # Assert that the mock KafkaProducer.send method was called
    assert mock_send.called

    # Assert that the response status code is 200
    assert response.status_code == 200

    # Assert that the response content is as expected
    assert response.content.decode('utf-8') == 'Message received and published to Kafka'