import os
import time
import subprocess
from pathlib import Path
import yaml
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


def start_docker_compose(yml_path: str) -> str:
    try:
        yml_file = Path(yml_path)
        if not yml_file.is_file():
            return f"Error: The specified file '{yml_path}' does not exist or is not a valid file."
        process = subprocess.Popen(
            ['docker-compose', 'up'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        while True:
            output = process.stdout.readline()
            if 'Application started. Press Ctrl+C to shut down.' in output:
                break
            if output == '' and process.poll() is not None:
                break
            return output
    except subprocess.CalledProcessError as e:
        return f"Error while starting containers: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def get_endpoint_from_docker_compose(yml_path: str) -> str:
    try:
        yml_file = Path(yml_path)
        if not yml_file.is_file():
            return f"Error: The specified file '{yml_path}' does not exist or is not a valid file."
        with open(yml_file, 'r') as file:
            compose_data = yaml.safe_load(file)
        return extract_endpoint_from_compose(compose_data)
    except yaml.YAMLError as e:
        return f"Error parsing YAML file: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def extract_endpoint_from_compose(compose_data: dict) -> str:
    services = compose_data.get('services', {})
    for service_name, service_config in services.items():
        ports = service_config.get('ports', [])
        for port_mapping in ports:
            if isinstance(port_mapping, str) and ':' in port_mapping:
                host_port, container_port = port_mapping.split(':')
                if container_port == '5050':
                    return f"http://localhost:{host_port}"
    return "Error: No service exposing port 5050 found in the docker-compose.yml file."


def get_key(azure_env_path: str) -> str:
    load_dotenv(azure_env_path)
    return os.getenv("azure_doc_intelligence_key")


def get_document_intelligence_client(endpoint, key):
    return DocumentAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))


def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result


def count_words_in_file(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
        words = text.split()
        return len(words)


def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (
                word.span.offset + word.span.length) <= (span.offset + span.length):
            return True
    return False


def get_results(result):
    document_info = {
        "handwritten": any([style.is_handwritten for style in result.styles]) if result.styles else False,
        "pages": [get_page_info(page) for page in result.pages],
        "tables": [get_table_info(table) for table in result.tables]
    }
    return document_info


def get_page_info(page):
    page_info = {
        "page_number": page.page_number,
        "width": page.width,
        "height": page.height,
        "unit": page.unit,
        "lines": [get_line_info(line) for line in page.lines],
        "selection_marks": [get_selection_mark_info(mark) for mark in page.selection_marks],
        "barcodes": [get_barcode_info(barcode) for barcode in page.barcodes]
    }
    return page_info


def get_line_info(line):
    return {
        "word_count": len(get_words(line)),
        "text": line.content,
        "polygon": line.polygon
    }


def get_selection_mark_info(mark):
    return {
        "state": mark.state,
        "polygon": mark.polygon,
        "confidence": mark.confidence
    }


def get_barcode_info(barcode):
    return {
        "value": barcode.value,
        "kind": barcode.kind,
        "confidence": barcode.confidence,
        "polygon": barcode.polygon
    }


def get_table_info(table):
    table_info = {
        "row_count": table.row_count,
        "column_count": table.column_count,
        "bounding_regions": [get_region_info(region) for region in table.bounding_regions],
        "cells": [get_cell_info(cell) for cell in table.cells]
    }
    return table_info


def get_region_info(region):
    return {
        "page_number": region.page_number,
        "polygon": region.polygon
    }


def get_cell_info(cell):
    return {
        "row_index": cell.row_index,
        "column_index": cell.column_index,
        "content": cell.content,
        "bounding_regions": [get_region_info(region) for region in cell.bounding_regions]
    }


def azure_document_intelligence_costs(pages: int) -> float:
    return 10 * (pages / 1_000)


def get_paragraphs(result):
    paragraphs = []
    for idx, paragraph in enumerate(result.paragraphs):
        item = {
            "id": "/paragraphs/" + str(idx),
            "content": paragraph.content if paragraph.content else "",
            "role": paragraph.role if paragraph.role else "",
            "polygon": paragraph.get("boundingRegions")[0]["polygon"],
            "pageNumber": paragraph.get("boundingRegions")[0]["pageNumber"]
        }
        paragraphs.append(item)
    return paragraphs


def get_tables(result):
    tables = []
    for table_idx, table in enumerate(result.tables):
        cells = []
        for cell in table.cells: 
            cells.append({
                "row_index": cell.row_index,
                "column_index": cell.column_index,
                "content": cell.content,
            })
        tab = {
            "row_count": table.row_count,
            "column_count": table.column_count,
            "cells": cells
        }
        tables.append(tab)
    return tables


def analyze_document(client, document_file):
    with open(document_file, "rb") as file:
        poller = client.begin_analyze_document("prebuilt-read", file.read())
        return poller.result()
