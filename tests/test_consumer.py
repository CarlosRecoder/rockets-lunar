import unittest
from unittest.mock import patch, MagicMock
from consumer import setup_logger

class TestConsumer(unittest.TestCase):

    @patch('consumer.MongoClient')
    @patch('consumer.KafkaConsumer')
    def test_process_message(self, MockKafkaConsumer, MockMongoClient):
        # Setup the mock KafkaConsumer
        mock_consumer = MockKafkaConsumer.return_value
        mock_consumer.__iter__.return_value = [MagicMock(value=b'{"metadata": {"channel": "193270a9-c9cf-404a-8f83-838e71d9ae67","messageNumber": 1,"messageTime": "2022-02-02T19:39:05.86337+01:00","messageType": "RocketLaunched"},"message": {"type": "Falcon-9","launchSpeed": 500,"mission": "ARTEMIS"}}')]

        # Setup the mock MongoClient
        mock_client = MockMongoClient.return_value
        mock_db = mock_client['rocket_data']
        mock_collection = mock_db['rocket_channels']
        mock_collection.insert_one.return_value = MagicMock()

        # Call the function to process messages
        process_message(mock_consumer, mock_db)

        # Verify that our MongoClient attempted to insert a document
        mock_collection.insert_one.assert_called_once()