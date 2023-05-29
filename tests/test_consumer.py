import unittest
from unittest.mock import patch, MagicMock
from bson.json_util import dumps
from app.consumer.consumer import RocketsConsumer

class TestConsumer(unittest.TestCase):

    @patch('app.consumer.consumer.KafkaConsumer')
    @patch('app.consumer.consumer.MongoClient')
    def setUp(self, mock_mongo_client, mock_kafka_consumer):
        # Mock MongoDB operations
        self.mock_db = mock_mongo_client.return_value['rocket_data']

        # Mock a Kafka message
        self.mock_message = MagicMock()
        self.mock_message.value.decode.return_value = dumps({"metadata": {"messageType": "type1", "messageNumber": "1", "messageTime": "time1", "channel": "channel1"}, "message": {"key": "value"}})
        # Create instance
        self.consumer_manager = RocketsConsumer(kafka_consumer=mock_kafka_consumer.return_value, mongo_client=mock_mongo_client.return_value)

    def test_process_message_new_channel(self):
        # Mock the return of find_one as None, indicating a new channel
        self.mock_db.rocket_channels.find_one.return_value = None

        # Call the function
        self.consumer_manager.process_message(self.mock_message)

        # Check that the expected MongoDB operations were called
        self.mock_db.rocket_channels.find_one.assert_any_call({'channel': 'channel1'})
        self.mock_db.rocket_channels.insert_one.assert_called_once_with({'channel': 'channel1', 'messages': []})
        self.mock_db.rocket_channels.update_one.assert_called_once_with(
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
        self.consumer_manager.consumer.commit.assert_called_once()

    def test_process_message_existing_channel(self):
        # Mock the return of find_one as a channel object, indicating an existing channel
        self.mock_db.rocket_channels.find_one.side_effect = [
            {'channel': 'channel1', 'messages': []},  # Mock finding the channel
            None  # Mock not finding the message in the channel
        ]

        # Call the function
        self.consumer_manager.process_message(self.mock_message)

        # Check that the expected MongoDB operations were called
        self.mock_db.rocket_channels.find_one.assert_any_call({'channel': 'channel1'})
        # The insert_one method should not be called for an existing channel
        self.mock_db.rocket_channels.insert_one.assert_not_called()
        self.mock_db.rocket_channels.update_one.assert_called_once_with(
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
        self.consumer_manager.consumer.commit.assert_called_once()
        
    
    def test_process_message_duplicate_message(self):
        # Mock the return of find_one as a channel object and a message object, indicating an existing channel and message
        self.mock_db.rocket_channels.find_one.side_effect = [
            {'channel': 'channel1', 'messages': []},  # Mock finding the channel
            {'channel': 'channel1', 'messages': [{'metadata': {'messageNumber': '1'}}]}  # Mock finding the message in the channel
        ]

        # Call the function
        self.consumer_manager.process_message(self.mock_message)

        # Check that the expected MongoDB operations were called
        self.mock_db.rocket_channels.find_one.assert_any_call({'channel': 'channel1'})
        # The insert_one and update_one methods should not be called for a duplicate message
        self.mock_db.rocket_channels.insert_one.assert_not_called()
        self.mock_db.rocket_channels.update_one.assert_not_called()

        # Check that the Kafka commit method was not called
        self.consumer_manager.consumer.commit.assert_not_called()



if __name__ == '__main__':
    unittest.main()
