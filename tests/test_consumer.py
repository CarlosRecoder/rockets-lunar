import unittest
from unittest.mock import patch, MagicMock
from bson.json_util import dumps
from app.consumer.consumer import process_message

class TestConsumer(unittest.TestCase):
    @patch('kafka.KafkaConsumer', autospec=True)
    @patch('pymongo.MongoClient', autospec=True)
    def test_process_message(self, mock_mongo_client, mock_kafka_consumer):
        # Mock a Kafka message
        mock_message = MagicMock()
        mock_message.value = dumps({"metadata": {"messageType": "type1", "messageNumber": "1", "messageTime": "time1", "channel": "channel1"}, "message": {"key": "value"}}).encode('utf-8')

        # Mock MongoDB operations
        mock_db = mock_mongo_client.return_value['rocket_data']
        mock_db.rocket_channels.find_one.return_value = None

        # Call the function
        process_message(mock_message)

        # Check that the expected MongoDB operations were called
        mock_db.rocket_channels.find_one.assert_any_call({'channel': 'channel1'})
        mock_db.rocket_channels.insert_one.assert_called_once_with({'channel': 'channel1', 'messages': []})
        mock_db.rocket_channels.update_one.assert_called_once_with(
            {'channel': 'channel1'},
            {'$push': {'messages': {
                'metadata': {
                    'messageNumber': '1',
                    'messageTime': 'time1',
                    'messageType': 'type1'
                },
                'message': {'key': 'value'}
            }}}
        )

        # Check that the Kafka commit method was called
        mock_kafka_consumer.return_value.commit.assert_called_once()