import os
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient, ExtractiveSummaryAction


def get_extractive_summary(document):
    load_dotenv()
    
    key = os.environ.get('LANGUAGE_KEY')
    endpoint = os.environ.get('LANGUAGE_ENDPOINT')

    client = authenticate_client(key, endpoint)


    poller = client.begin_analyze_actions(
        [document],
        actions=[
            ExtractiveSummaryAction(max_sentence_count=4)
        ],
    )

    document_results = poller.result()

    global_summary = ""
    for result in document_results:
        extract_summary_result = result[0]
        global_summary += " ".join([sentence.text for sentence in extract_summary_result.sentences])

    return global_summary



def authenticate_client(key, endpoint):
    ta_credential = AzureKeyCredential(key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
    return text_analytics_client


def get_abstractive_summary(document):
    load_dotenv()

    key = os.environ.get('LANGUAGE_KEY')
    endpoint = os.environ.get('LANGUAGE_ENDPOINT')

    text_analytics_client = TextAnalyticsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key),
    )

    poller = text_analytics_client.begin_abstract_summary([document])
    abstract_summary_results = poller.result()

    output = ""
    for result in abstract_summary_results:
        if result.kind == "AbstractiveSummarization":
            for summary in result.summaries:
                output += summary.text

    return output