import unittest
import requests

class TestOllamaService(unittest.TestCase):
    def test_estimae_tokens(self):
        text = "FastAPI will use this response_model to do all the data documentation, validation, etc"
        response = requests.post("http://localhost:8000/estimate_tokens/", json={"content": text})
        nb_tokens = int(response.json()["nb_tokens"])
        self.assertEqual(nb_tokens, 16)

if __name__ == '__main__':
    unittest.main()