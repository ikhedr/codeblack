from dashboard.app import CodeBlack
import json
import requests
import unittest

headers = {'content-type': 'application/json'}


class TestCodeBlack(unittest.TestCase):
    def __init__(self):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_check_correct_transfer_order(self):
        to_response = requests.post("http://127.0.0.1:5000/check_transfer_order",
                                    data=json.dumps({"to_number": "2003615877"}), headers=headers)
        to_response = json.loads(to_response.text)
        self.assertEqual(to_response, 'success')

    def test_check_incorrect_transfer_order(self):
        to_response = requests.post("http://127.0.0.1:5000/check_transfer_order",
                                    data=json.dumps({"to_number": "1"}), headers=headers)
        to_response = json.loads(to_response.text)
        self.assertEqual(to_response, 'failure')

    def test_update_product_details(self):
        to_response = requests.post("http://127.0.0.1:5000/update_product_details",
                                    data=json.dumps({"to_number": "2003615877", "dest__bin": "B1001",
                                                     "material": "Rings"}), headers=headers)
        to_response = json.loads(to_response.text)
        self.assertEqual(to_response, 'success')


if __name__ == '__main__':
    unittest.main()
