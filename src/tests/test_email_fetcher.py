import unittest
from unittest.mock import MagicMock
from src.gmail_reader.email_fetcher import list_messages

class TestEmailFetcher(unittest.TestCase):
    def setUp(self):
        # Set up a mock service object
        self.mock_service = MagicMock()

    def test_list_messages_success(self):
        # Mock the API response
        self.mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': '1', 'threadId': 't1'},
                {'id': '2', 'threadId': 't2'},
            ]
        }

        # Call the function
        messages = list_messages(self.mock_service)

        # Assertions
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['id'], '1')
        self.assertEqual(messages[1]['threadId'], 't2')

    def test_list_messages_no_messages(self):
        # Mock the API response with no messages
        self.mock_service.users().messages().list().execute.return_value = {}

        # Call the function
        messages = list_messages(self.mock_service)

        # Assertions
        self.assertEqual(len(messages), 0)

    def test_list_messages_error(self):
        # Simulate an error
        self.mock_service.users().messages().list.side_effect = Exception("API error")

        # Call the function
        messages = list_messages(self.mock_service)

        # Assertions: The function should return an empty list when an error occurs
        self.assertEqual(messages, [])

if __name__ == '__main__':
    unittest.main()