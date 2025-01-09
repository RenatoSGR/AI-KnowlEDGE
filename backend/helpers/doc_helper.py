# backend/utils.py

import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

def get_result(file_content):
    load_dotenv()
    
    endpoint = os.getenv("AZURE_DOCUMENT_ANALYSIS_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_ANALYSIS_KEY")


    azure_document_intelligence_client = DocumentAnalysisClient(
        endpoint=endpoint, 
        credential=AzureKeyCredential(key)
    )
    poller = azure_document_intelligence_client.begin_analyze_document("prebuilt-read", file_content)
    result = poller.result()

    return "\n".join(get_paragraphs(result))


def get_paragraphs(result):
    paragraphs = []
    for paragaraph in result.paragraphs:
        paragraphs.append(paragaraph.content)
    return paragraphs


def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (
                word.span.offset + word.span.length) <= (span.offset +
                                                         span.length):
            return True
    return False


def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result


def has_handwritten_content(result):
    if result.styles and any([style.is_handwritten for style in result.styles]):
        return True
    else:
        return False


def analyze_page_layout(page):
    layout_info = []
    layout_info.append(f"*** Analyzing layout from page #{page.page_number} ***")
    layout_info.append(f"Page has width: {page.width} and height: {page.height}, measured with unit: {page.unit}")
    layout_info.append("")
    return "\n".join(layout_info)


def analyze_lines(page):
    lines_info = []
    if page.lines:
        for line_idx, line in enumerate(page.lines):
            words = get_words(page, line)
            lines_info.append(
                f"\n- Line # {line_idx} has word count {len(words)} and text '{line.content}' "
                f"within bounding polygon '{line.polygon}'"
            )
            for word in words:
                lines_info.append(f"  - Word: {word.content}")
    return "\n".join(lines_info)


def check_handwritten_content(result):
    if result.styles and any([style.is_handwritten for style in result.styles]):
        return "Document contains handwritten content"
    else:
        return "Document does not contain handwritten content"


def analyze_page(page):
    page_analysis = [
        f"----Analyzing layout from page #{page.page_number}----",
        f"Page has width: {page.width} and height: {page.height}, measured with unit: {page.unit}"
    ]

    if page.lines:
        for line_idx, line in enumerate(page.lines):
            words = get_words(page, line)
            page_analysis.append(
                f"...Line # {line_idx} has word count {len(words)} and text '{line.content}' "
                f"within bounding polygon '{line.polygon}'"
            )
            for word in words:
                page_analysis.append(
                    f"......Word '{word.content}' has a confidence of {word.confidence}"
                )

    if page.selection_marks:
        for selection_mark in page.selection_marks:
            page_analysis.append(
                f"Selection mark is '{selection_mark.state}' within bounding polygon "
                f"'{selection_mark.polygon}' and has a confidence of {selection_mark.confidence}"
            )

    return "\n".join(page_analysis)


def analyze_table(table_idx, table):
    table_analysis = [
        f"Table # {table_idx} has {table.row_count} rows and {table.column_count} columns"
    ]
    if table.bounding_regions:
        for region in table.bounding_regions:
            table_analysis.append(
                f"Table # {table_idx} location on page: {region.page_number} is {region.polygon}"
            )
    for cell in table.cells:
        table_analysis.append(
            f"...Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'"
        )
        if cell.bounding_regions:
            for region in cell.bounding_regions:
                table_analysis.append(
                    f"...content on page {region.page_number} is within bounding polygon '{region.polygon}'"
                )

    return "\n.join(table_analysis)"