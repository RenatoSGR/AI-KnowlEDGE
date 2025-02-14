import unittest
import requests

class TestOllamaService(unittest.TestCase):

    
    def test_estimae_tokens(self):
        text = "FastAPI will use this response_model to do all the data documentation, validation, etc"
        response = requests.post("http://localhost:8000/estimate_tokens/", json={"content": text})
        nb_tokens = int(response.json()["nb_tokens"])
        
        self.assertEqual(nb_tokens, 16)


    def test_available_models(self):
        available_models = requests.get("http://localhost:8000/get_models/").json()["available_models"]
        
        self.assertIsInstance(available_models, list)


    def test_generate_questions(self):
        model_name = "phi3.5:latest"
        text = "FastAPI will use this response_model to do all the data documentation, validation, etc"
        response = requests.post("http://localhost:8000/generate_questions/", json={"model_name": model_name, "content": text})
        questions = response.json()["questions"]

        self.assertIsInstance(questions, list)


    def test_generate_answer(self):
        question = "1. What is the primary responsibility of a Technical Lead at Microsoft, and how have you contributed to delivering innovative solutions in your decade-long tenure at the company?"
        relevant_chunks = ['Professional Summary\nWith a decade of experience in the tech industry, I have honed my skills as a Technical Lead at Microsoft, leading diverse teams to deliver innovative solutions. My expertise lies in software development, system architecture, and team management, driving projects from conception to successful deployment.\nProfessional Experience\nMicrosoft, Technical Lead\nJanuary 2015 - Present\n· Lead a team of 20+ engineers in designing and developing cutting-edge software solutions.', '. Received the Microsoft Excellence Award for outstanding leadership and innovation in 2019.\nMicrosoft, Senior Software Engineer\nJune 2010 - December 2014\n. Contributed to the development of key software components in major product releases.\n· Designed and implemented scalable system architectures and APIs.\n· Conducted code reviews and provided technical guidance to ensure code quality and maintainability.', 'Raoui Lassoued\nTechnical Lead at Microsoft\nContact Information\n. Email: raoui.lassoued@example.com\n· Phone: (123) 456-7890\n· Linkedln: linkedin.com/in/raoui-lassoued\n· Address: 1234 Tech Lane, Seattle, WA, 98101\nProfessional Summary']
        model_name = "phi3.5:latest"

        answer = requests.post(
            "http://localhost:8000/generate_answer", 
            json={"question": question, "relevant_chunks": relevant_chunks, "model_name": model_name}
        ).json()["answer"]

        self.assertIsInstance(answer, dict)




if __name__ == '__main__':
    unittest.main()