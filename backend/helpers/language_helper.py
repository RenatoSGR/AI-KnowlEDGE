import os
import re
import time
import requests

from urllib.parse import urlparse
from dotenv import load_dotenv


load_dotenv()
API_ENDPOINT = os.environ.get('LANGUAGE_ENDPOINT')
API_KEY = os.environ.get('LANGUAGE_KEY')


def get_extractive_summary(document):
    response = start_analyze_text_job(document)
    job_id = parse_http_header(response.headers, response.status_code)
    if job_id:
        job_result = fetch_job_result(job_id)
        return extract_paragraph_from_result(job_result)
    else:
        raise Exception("Failed to retrieve job ID")
    

def extract_job_id(operation_location):
    parsed_url = urlparse(operation_location)
    match = re.search(r'/jobs/([^/?]+)', parsed_url.path)
    return match.group(1) if match else None


def get_analyze_text_job(job_id):
    url = f"{API_ENDPOINT}/language/analyze-text/jobs/{job_id}?api-version=2023-04-01"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": API_KEY
    }
    response = requests.get(url, headers=headers)
    return response.json()


def parse_http_header(headers, status_code):
    operation_location = headers.get('Operation-Location')
    if status_code == 202 and operation_location:
        return extract_job_id(operation_location)
    return None


def fetch_job_result(job_id):
    while True:
        job_result = get_analyze_text_job(job_id)
        status = job_result.get('status')
        if status == 'succeeded':
            return job_result
        elif status in ['failed', 'cancelled']:
            raise Exception(f"Job {status}")
        time.sleep(2)


def extract_paragraph_from_result(job_result):
    paragraph = ""
    for item in job_result['tasks']['items']:
        for document in item['results']['documents']:
            for sentence in document['sentences']:
                paragraph += sentence['text']
    return paragraph



def start_analyze_text_job(document):
    url = f"{API_ENDPOINT}/language/analyze-text/jobs?api-version=2023-04-01"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": API_KEY
    }
    data = {
        "displayName": "Text Extractive Summarization",
        "analysisInput": {
            "documents": [
                {
                    "id": "1",
                    "language": "en",
                    "text": document
                }
            ]
        },
        "tasks": [
            {
                "kind": "ExtractiveSummarization",
                "taskName": "Text Extractive Summarization Task 1"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response
