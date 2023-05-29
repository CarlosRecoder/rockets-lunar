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

    class MockFuture:
        def get(self, timeout=None):
            return MockRecordMetadata()

    class MockRecordMetadata:
        topic = 'test_topic'
    
    # Use patch to replace KafkaProducer.send with a Mock object
    with patch('kafka.KafkaProducer.send', return_value=MockFuture()) as mock_send:
        
        # Make a POST request to the /messages endpoint with the test message
        response = client.post('/messages', json=test_message)

    # Assert that the mock KafkaProducer.send method was called
    assert mock_send.called

    # Assert that the response status code is 200
    assert response.status_code == 200

    # Assert that the response content is as expected
    assert response.json() == 'Message received and published to Kafka'